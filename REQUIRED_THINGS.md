# 📋 Quantum Mind — Live Launch Service Requirements

To run the **Quantum Mind** hypnotherapy platform live in production for your customers, you need to sign up for and configure **4 external services**. 

This document lists the exact accounts, recommended subscription plans, signup links, and estimated monthly costs in plain English.

---

## 📊 Summary of Services & Startup Costs

| Service | Primary Purpose | Recommended Plan to Choose | Estimated Monthly Cost |
| :--- | :--- | :--- | :--- |
| **1. AWS (Amazon Web Services)** | Hosts your secure database, main API servers, and stores generated MP3 files. | **Free Tier Account** (using micro-sized server instances). | **$15 – $30 / month** |
| **2. Anthropic (Claude AI)** | The "AI Therapist" that writes the personalized session scripts. | **Developer Console API** (Pay-As-You-Go). | **$10 – $20 initial deposit** (fractions of a cent per use) |
| **3. ElevenLabs** | The "Voice Actor" that turns the text script into highly realistic audio. | **Creator Plan** *(Required for Commercial Rights to sell sessions)*. | **$22 / month** |
| **4. Custom Domain Name** | Your unique web address (e.g., `quantum-mind.com`). | Standard Domain Registration (`.com`). | **$10 – $15 / year** (~$1/month) |

### 💰 Total Estimated Launch Budget: **~$40 to $50 per month**

---

## 🔍 Detailed Account Breakdowns

### 1. ☁️ AWS (Amazon Web Services)
* **Why you need it**: This hosts the actual backend software, database, and final audio storage. It keeps user data secure and streams the MP3 files to your users' devices.
* **Signup URL**: [https://aws.amazon.com](https://aws.amazon.com)
* **Plan to Choose**: Register for a standard personal or business account. The Terraform code we set up will automatically select the smallest, cheapest server sizes (like `t3.micro` which are Free Tier eligible).
* **Expected Cost**: Under **$30/month** to support your first few hundred users.

### 2. 🧠 Anthropic (Claude AI)
* **Why you need it**: Reads the user’s clinical intake form and writes the tailored 11-phase hypnotherapy scripts.
* **Signup URL**: [https://console.anthropic.com](https://console.anthropic.com)
* **Plan to Choose**: Create a Developer API Account. It works like a prepaid phone: you pre-load it with $10 or $20 via credit card, and it deducts a tiny fee based on the length of each script generated.
* **Expected Cost**: Roughly **$0.05 to $0.15** per session script created.

### 3. 🎙️ ElevenLabs
* **Why you need it**: Takes the text script written by Claude and converts it into a realistic, calming voice.
* **Signup URL**: [https://elevenlabs.io](https://elevenlabs.io)
* **Plan to Choose**: **Creator Plan ($22/month)**.
  * *Important Note*: You **must** select the Creator Plan. The Free and Starter plans do **not** grant you the legal right to charge customers or sell generated audio files (commercial license). The Creator Plan includes commercial usage rights and 100,000 text-to-speech characters per month.
* **Expected Cost**: **$22/month** flat (upgradeable if you scale up).

### 4. 🌐 Domain Registrar (e.g., Namecheap or GoDaddy)
* **Why you need it**: Provides a clean and professional web address (e.g., `api.quantum-mind.com`) instead of a complicated technical string of numbers.
* **Signup URL**: [https://www.namecheap.com](https://www.namecheap.com) or Route 53 in AWS.
* **Plan to Choose**: Standard `.com` or `.app` domain registration.
* **Expected Cost**: **$10 – $15 per year**.

---

## 🏁 Step-by-Step Action Items for Launch

Once you sign up for these accounts, here is what you need to extract and hand over to your developer (or paste into your AWS Secrets Manager vault):

1. **AWS credentials**: Access Key ID and Secret Access Key.
2. **Anthropic API Key**: Found in your Anthropic Console dashboard (starts with `sk-ant-api...`).
3. **ElevenLabs API Key**: Found in your ElevenLabs Profile Settings page.
4. **ElevenLabs Voice ID**: Select the voice you want to use (e.g., "Rachel" or a custom voice you cloned) and get its Voice ID code.
5. **Domain Registrar Login**: To point your domain to the AWS servers.
