import mongoose from 'mongoose';
import { MongoMemoryServer } from 'mongodb-memory-server';

let memoryServer;

const Connection = async (username, password) => {
    let URL = process.env.MONGODB_URI;

    if (!URL && username && password) {
        URL = `mongodb+srv://${username}:${password}@cluster0.jjowu.mongodb.net/flipkart?retryWrites=true&w=majority`;
    }

    try {
        if (!URL) {
            memoryServer = await MongoMemoryServer.create();
            URL = memoryServer.getUri();
            console.log('Using in-memory MongoDB for local development');
        }

        await mongoose.connect(URL, { useUnifiedTopology: true, useNewUrlParser: true, useFindAndModify: false });
        console.log('Database Connected Succesfully');
    } catch (error) {
        console.error('Database connection failed:', error.message);
        if (!memoryServer) {
            try {
                memoryServer = await MongoMemoryServer.create();
                const fallbackURL = memoryServer.getUri();
                await mongoose.connect(fallbackURL, { useUnifiedTopology: true, useNewUrlParser: true, useFindAndModify: false });
                console.log('Database Connected to in-memory MongoDB fallback');
            } catch (fallbackError) {
                console.error('In-memory MongoDB fallback failed:', fallbackError.message);
            }
        }
    }
};

export default Connection;