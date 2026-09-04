import React, { useState } from 'react';
import { Box, Button, CircularProgress, Paper, TextField, Typography, makeStyles } from '@material-ui/core';
import SearchIcon from '@material-ui/icons/Search';
import AndroidIcon from '@material-ui/icons/Android';
import ShoppingCartIcon from '@material-ui/icons/ShoppingCart';
import ImageSearchIcon from '@material-ui/icons/ImageSearch';
import { approveBuyerAgentPurchase, getBuyerPaymentKey, getBuyerTransaction, requestBuyerAgentPurchase, searchBuyerAgentImage, searchWithBuyerAgent, verifyBuyerPayment } from '../service/api';

const useStyles = makeStyles((theme) => ({
    panel: {
        margin: '18px 0',
        padding: theme.spacing(2.5),
        borderRadius: 2,
        border: '1px solid #d7e2ec',
        background: 'linear-gradient(120deg, #f7fbff 0%, #fff 70%)'
    },
    title: { display: 'flex', alignItems: 'center', gap: theme.spacing(1), color: '#172b4d' },
    form: { display: 'flex', gap: theme.spacing(1.5), alignItems: 'flex-start', marginTop: theme.spacing(2), [theme.breakpoints.down('sm')]: { flexDirection: 'column' } },
    query: { flex: 1, minWidth: 220 },
    budget: { width: 150, [theme.breakpoints.down('sm')]: { width: '100%' } },
    actions: { display: 'flex', gap: theme.spacing(1), [theme.breakpoints.down('sm')]: { width: '100%', '& button': { flex: 1 } } },
    result: { marginTop: theme.spacing(2), padding: theme.spacing(1.5), background: '#fff', borderLeft: '3px solid #2874f0' },
    status: { marginTop: theme.spacing(1), color: '#425466' }
}));

const getBuyerError = (error) => {
    if (!error.response) return 'AI buyer agent is offline. Start it on port 8001 and try again.';
    const detail = error.response.data?.detail;
    if (Array.isArray(detail)) return detail.map((item) => item.msg).join(', ');
    return detail || `AI buyer request failed (${error.response.status}).`;
};

const AiBuyerPanel = () => {
    const classes = useStyles();
    const [query, setQuery] = useState('wireless headphones under 25000');
    const [budget, setBudget] = useState('25000');
    const [result, setResult] = useState(null);
    const [status, setStatus] = useState('');
    const [loading, setLoading] = useState(false);
    const [image, setImage] = useState(null);

    const runSearch = async () => {
        if (!query.trim()) return;
        setLoading(true);
        setStatus('Finding the best match...');
        try {
            const response = await searchWithBuyerAgent(query);
            setResult(response.data);
            setStatus(`${response.data.total_found} match${response.data.total_found === 1 ? '' : 'es'} found`);
        } catch (error) {
            setResult(null);
            setStatus(getBuyerError(error));
        } finally {
            setLoading(false);
        }
    };

    const requestPurchase = async () => {
        if (!query.trim()) return;
        setLoading(true);
        setStatus('The AI buyer is evaluating this purchase...');
        try {
            const response = await requestBuyerAgentPurchase(query, Number(budget));
            setResult(response.data);
            setStatus(response.data.message || response.data.status);
            if (response.data.status === 'payment_initiated') {
                const transaction = await getBuyerTransaction(response.data.transaction_id);
                await openCheckout(response.data, transaction.data);
            }
        } catch (error) {
            setStatus(getBuyerError(error));
        } finally {
            setLoading(false);
        }
    };

    const searchImage = async () => {
        if (!image) return;
        setLoading(true);
        setStatus('Reading the product image...');
        try {
            const response = await searchBuyerAgentImage(image);
            setResult(response.data);
            setStatus(`${response.data.total_found} image match${response.data.total_found === 1 ? '' : 'es'} found`);
        } catch (error) {
            setResult(null);
            setStatus(getBuyerError(error));
        } finally {
            setLoading(false);
        }
    };

    const approvePurchase = async () => {
        setLoading(true);
        setStatus('Submitting approval and creating the payment order...');
        try {
            const response = await approveBuyerAgentPurchase(result.transaction_id);
            const transaction = await getBuyerTransaction(result.transaction_id);
            const updatedResult = { ...result, ...response.data, payment: { order_id: transaction.data.razorpay_order?.id, amount_inr: transaction.data.amount_paise / 100, currency: transaction.data.currency } };
            setResult(updatedResult);
            setStatus(response.data.message);
            await openCheckout(updatedResult, transaction.data);
        } catch (error) {
            setStatus(getBuyerError(error));
        } finally {
            setLoading(false);
        }
    };

    const openCheckout = async (purchase, transaction) => {
        const keyResponse = await getBuyerPaymentKey();
        await new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://checkout.razorpay.com/v1/checkout.js';
            script.onload = resolve;
            script.onerror = () => reject(new Error('Razorpay Checkout failed to load'));
            document.body.appendChild(script);
        });
        const checkout = new window.Razorpay({
            key: keyResponse.data.key_id,
            config_id: 'config_TXtxsjGGWfBHHr',
            amount: transaction.amount_paise,
            currency: transaction.currency,
            name: 'AI Buyer Agent',
            description: transaction.product_name,
            order_id: transaction.razorpay_order.id,
            prefill: { email: 'janmayswami@gmail.com' },
            handler: async (payment) => {
                const verified = await verifyBuyerPayment({
                    transaction_id: purchase.transaction_id,
                    razorpay_order_id: payment.razorpay_order_id,
                    razorpay_payment_id: payment.razorpay_payment_id,
                    razorpay_signature: payment.razorpay_signature
                });
                setResult({ ...purchase, status: verified.data.status });
                setStatus(verified.data.message);
            }
        });
        checkout.on('payment.failed', (payment) => setStatus(payment.error?.description || 'Payment failed'));
        checkout.open();
    };

    const product = result?.products?.[0]?.product || result?.product;

    return (
        <Paper className={classes.panel} elevation={0}>
            <Typography variant="h6" className={classes.title}>
                <AndroidIcon color="primary" /> AI Buyer
            </Typography>
            <Typography variant="body2" color="textSecondary">
                Describe what you want and let the buyer agent search its catalog or request a guarded purchase.
            </Typography>
            <Box className={classes.form}>
                <TextField className={classes.query} label="What should I buy?" value={query} onChange={(event) => setQuery(event.target.value)} variant="outlined" size="small" />
                <TextField className={classes.budget} label="Budget (INR)" value={budget} onChange={(event) => setBudget(event.target.value)} type="number" variant="outlined" size="small" inputProps={{ min: 1 }} />
                <Box className={classes.actions}>
                    <Button variant="outlined" color="primary" startIcon={<SearchIcon />} onClick={runSearch} disabled={loading}>Search</Button>
                    <Button variant="contained" color="primary" startIcon={<ShoppingCartIcon />} onClick={requestPurchase} disabled={loading}>Request purchase</Button>
                </Box>
            </Box>
            <Box className={classes.form}>
                <input accept="image/jpeg,image/png,image/webp" type="file" onChange={(event) => setImage(event.target.files[0] || null)} />
                <Button variant="outlined" color="primary" startIcon={<ImageSearchIcon />} onClick={searchImage} disabled={!image || loading}>Search image</Button>
                <Typography variant="caption" color="textSecondary">Receipt: janmayswami@gmail.com</Typography>
            </Box>
            {loading && <CircularProgress size={20} />}
            {status && <Typography variant="body2" className={classes.status}>{status}</Typography>}
            {product && (
                <Box className={classes.result}>
                    <Typography variant="subtitle1">{product.name}</Typography>
                    <Typography variant="body2">{product.brand || product.category || 'AI catalog match'} {product.price_inr ? `· ₹${product.price_inr}` : ''}</Typography>
                    {result.ai_explanation && <Typography variant="body2" color="textSecondary">{result.ai_explanation}</Typography>}
                    {result.transaction_id && <Typography variant="caption" color="textSecondary">Transaction: {result.transaction_id}</Typography>}
                    {result.status === 'pending_approval' && (
                        <>
                            <Typography variant="body2" color="textSecondary">No receipt is sent yet. Approve the purchase, complete Razorpay payment, and the receipt will be emailed to janmayswami@gmail.com.</Typography>
                            <Button variant="contained" color="secondary" onClick={approvePurchase} disabled={loading}>Approve purchase</Button>
                        </>
                    )}
                    {result.status === 'completed' && <Typography variant="body2" color="textSecondary">Payment completed. Receipt delivery was requested for janmayswami@gmail.com.</Typography>}
                </Box>
            )}
        </Paper>
    );
};

export default AiBuyerPanel;