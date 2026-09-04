import Product from '../model/productSchema.js';
import sampleProducts from '../data/sampleProducts.js';

const ensureSampleProducts = async () => {
    const existingProducts = await Product.find({}, { id: 1 }).lean();
    const existingIds = new Set(existingProducts.map(product => product.id));
    const missingProducts = sampleProducts.filter(product => !existingIds.has(product.id));

    if (missingProducts.length > 0) {
        await Product.insertMany(missingProducts);
        console.log(`Seeded ${missingProducts.length} new sample products into database`);
    }

    await Promise.all(sampleProducts.map(product => Product.updateOne(
        { id: product.id },
        { $set: { url: product.url, detailUrl: product.detailUrl } }
    )));
};

export const getProducts = async (request, response) => {
    try {
        await ensureSampleProducts();
        const products = await Product.find({});
        response.json(products);
    } catch (error) {
        console.error('Error fetching products:', error.message);
        response.status(500).json({ message: 'Failed to load products' });
    }
};

export const getProductById = async (request, response) => {
    try {
        await ensureSampleProducts();
        const products = await Product.findOne({ 'id': request.params.id });
        response.json(products);
    } catch (error) {
        console.error('Error fetching product by id:', error.message);
        response.status(500).json({ message: 'Failed to load product details' });
    }
};