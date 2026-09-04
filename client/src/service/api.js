import axios from 'axios';

const url = 'http://localhost:8000';
const buyerAgentUrl = process.env.REACT_APP_BUYER_AGENT_URL || 'http://localhost:8001';

export const searchWithBuyerAgent = async (query, userId = 'flipkart_demo_user') => {
    return axios.post(`${buyerAgentUrl}/search`, {
        query,
        user_id: userId,
        max_results: 5,
        filters: { in_stock_only: true }
    });
};

export const requestBuyerAgentPurchase = async (query, maxBudget, userId = 'flipkart_demo_user') => {
    return axios.post(`${buyerAgentUrl}/purchase`, {
        query,
        user_id: userId,
        max_budget: maxBudget || undefined,
        require_approval: true,
        receipt_email: 'janmayswami@gmail.com'
    });
};

export const searchBuyerAgentImage = async (image, userId = 'flipkart_demo_user') => {
    const formData = new FormData();
    formData.append('image', image);
    formData.append('user_id', userId);
    return axios.post(`${buyerAgentUrl}/search/image`, formData);
};

export const approveBuyerAgentPurchase = async (transactionId, approverId = 'human_reviewer') => {
    return axios.post(`${buyerAgentUrl}/approve/${transactionId}`, {
        transaction_id: transactionId,
        approved: true,
        approver_id: approverId
    });
};

export const getBuyerTransaction = async (transactionId) => {
    return axios.get(`${buyerAgentUrl}/transactions/detail/${transactionId}`);
};

export const getBuyerPaymentKey = async () => {
    return axios.get(`${buyerAgentUrl}/payment/key`);
};

export const verifyBuyerPayment = async (payment) => {
    return axios.post(`${buyerAgentUrl}/payment/verify`, payment);
};

export const authenticateLogin = async (user) => {
    try {
        return  await axios.post(`${url}/login`, user) 
    } catch (error) {
        console.log('error while calling login API: ', error);
    }
}

export const authenticateSignup = async (user) => {
    try {
        return await axios.post(`${url}/signup`, user)
    } catch (error) {
        console.log('error while calling Signup API: ', error);
    }
}

export const getProductById = async (id) => {
    try {
        return await axios.get(`${url}/product/${id}`);
    } catch (error) {
        console.log('Error while getting product by id response', error);
    }
}

export  const payUsingPaytm = async (data) => {
    try {
        console.log('payment api');
        let response = await axios.post(`${url}/payment`, data);
        console.log(response.data);
        return response.data;
    } catch (error) {
        console.log('error', error);
    }
}

