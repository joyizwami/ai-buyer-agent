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
   


![Screenshot from 2021-11-01 18-05-31](https://user-images.githubusercontent.com/91063960/139678469-c631005a-9c20-4321-8022-24f4573427b7.png)
![Screenshot from 2021-11-01 18-05-52](https://user-images.githubusercontent.com/91063960/139678483-ca95e74e-44a5-422c-9cac-4bfe463215ef.png)
![Screenshot from 2021-11-01 18-06-08](https://user-images.githubusercontent.com/91063960/139678489-03130e57-7e0b-4bb0-96f6-f4ec85b8efbe.png)
![Screenshot from 2021-11-01 18-06-32](https://user-images.githubusercontent.com/91063960/139678548-e58c550e-51c5-4695-a0c3-d6563737548a.png)
![Screenshot from 2021-11-01 18-07-35](https://user-images.githubusercontent.com/91063960/139678663-177aedd5-e622-4441-871b-e0af7be1e363.png)
![Screenshot from 2021-11-01 18-08-34](https://user-images.githubusercontent.com/91063960/139678729-432bb265-9d98-4a2d-8c27-d66eb2f09b26.png)
![Screenshot from 2021-11-01 18-08-40](https://user-images.githubusercontent.com/91063960/139678735-0ac4e3e8-591d-4652-8965-22c830fa94db.png)
![Screenshot from 2021-11-01 18-09-33](https://user-images.githubusercontent.com/91063960/139678737-8d069f75-9d7f-44ff-8e37-4be34ebc95cd.png)

  
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
