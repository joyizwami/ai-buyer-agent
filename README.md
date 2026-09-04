# AI Buyer Agent Commerce Demo

One monorepo containing a Flipkart-style storefront and an AI Buyer Agent that searches the storefront catalog, enforces budget and approval policy, creates Razorpay test orders, verifies payment, and queues receipt email delivery.

## Project Layout

- `client/`: React storefront and AI Buyer panel
- `server/`: Flipkart Express API and MongoDB product service
- `ai-buyer-agent/`: FastAPI buyer, policy, Razorpay, receipt, and image-search service

## Run Locally

### 1. Flipkart API

```powershell
cd server
npm install
npm start
```

Runs on `http://localhost:8000`.

### 2. AI Buyer Agent

Copy `ai-buyer-agent/.env.example` to `ai-buyer-agent/.env` and add local test credentials. Keep `.env` untracked.

```powershell
cd ai-buyer-agent
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Runs on `http://localhost:8001`.

### 3. React client

```powershell
cd client
npm install
npm start
```

Open `http://localhost:3000`.

## Demo Flow

1. Search for a product from the Flipkart catalog in the AI Buyer panel.
2. Request purchase and review the AI selection and policy decision.
3. Approve higher-value purchases.
4. Complete the Razorpay test checkout.
5. Verify the transaction and receipt workflow.

Razorpay must remain in test mode for local demos. Never commit API keys, SMTP passwords, or other secrets.
# Flipkar Clone MERN stack 

Sijeesh Miziha's Flipkart Clone is done with top-notch features for the entrepreneur startups like Flipkart it has RazorPay Integration and get money from anywhere. This Flipkart clone with the best features in mobile, web, and iOS platforms, Completely responsive design using Material UI.
- 🧪 **Kindly Please Support Me**
  - I can provide brand-free products and full technical support for 1 year along with 1-year free update support and moreover
- 👁 **Well typed**
  - Clean JavaScript code with good folder structure.,
- 📄 **Well documented**
  - I can provide full reference & installation documentation alongside detailed guides through my Youtube Channel Sijeesh Miziha feel free to subscribe 
  - If You supporting me., then I can also create the full lecture video from the scratch..,you can learn React.js as beginer 
- **Requirements to fork this repo**
   - Strong knowledge of JavaScript
   - React js, redux , redux-thunk , context
   - Knowledge of Express js & MVC architecture
   - Basic knowledge in MongoDB & Mongoose
   
![image alt](https://github.com/joyizwami/ai-buyer-agent/blob/13eb48078b84907f2fcf514782c916f08c3b0138/Screenshot%202026-09-04%20151708.png)
![image alt](https://github.com/joyizwami/ai-buyer-agent/blob/341f117a0abdee16aa74918ee7c36723cbf2d54a/Screenshot%202026-09-04%20151727.png)
![image alt](https://github.com/joyizwami/ai-buyer-agent/blob/13eb48078b84907f2fcf514782c916f08c3b0138/Screenshot%202026-09-04%20151743.png)
![image alt](https://github.com/joyizwami/ai-buyer-agent/blob/13eb48078b84907f2fcf514782c916f08c3b0138/Screenshot%202026-09-04%20151839.png)
![image alt](https://github.com/joyizwami/ai-buyer-agent/blob/13eb48078b84907f2fcf514782c916f08c3b0138/Screenshot%202026-09-04%20151854.png)
![image alt](https://github.com/joyizwami/ai-buyer-agent/blob/13eb48078b84907f2fcf514782c916f08c3b0138/Screenshot%202026-09-04%20152020.png)
Flipkart is one of the best and trending eCommerce sites with a presence throughout India. The online shopping website is for Buying and Selling products online within the network.

Sijeesh Miziha's Flipkart clone is a ready-made remarkable multi-vendor eCommerce site built-in compleatly JavaScript that helps Entrepreneurs can start their own business like Flipkart, which allows the vendors to add products & users to buy the products easily with just a click.
## Tech Stack

  - **MERN STACK** 
  - **React js , Node js , MongoDB , Express js** 
  - **Materiel UI**
  - **RazorPay integration**  



  
## Installation

  1. Clone/Download the repo.
  2. Run npm install on client as well as server.
  3. Run npm start both server and  client  to spin the up the local dev server port 8000,3000,(http://localhost:8000),(http://localhost:3000).
