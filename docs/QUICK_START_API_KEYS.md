# Quick Start: Obtain API Keys

**⏱️ Time Required**: 10-15 minutes (excluding DrugBank approval wait time)

---

## 🚀 Quick Steps

### Step 1: Get Anthropic API Key (REQUIRED - 5 minutes)

1. **Visit**: https://console.anthropic.com/
2. **Sign up/Login** with email or Google
3. **Click**: "API Keys" in sidebar
4. **Click**: "Create Key" button
5. **Copy**: The key (starts with `sk-ant-...`)
6. **Save**: In password manager for safekeeping

✅ **You're done!** Store this key in `.env` file (coming in next task US-004)

---

### Step 2: Get NCBI API Key (OPTIONAL but recommended - 3 minutes)

1. **Visit**: https://www.ncbi.nlm.nih.gov/account/
2. **Create account** or login
3. **Go to**: Settings → API Key Management
4. **Click**: "Create an API Key"
5. **Copy**: The generated key
6. **Save**: In password manager

✅ **Done!** This increases PubMed rate limits from 3/sec to 10/sec

---

### Step 3: DrugBank API (OPTIONAL - can skip for MVP)

**Option A: Use Mock Data (Recommended for MVP)**
- ✅ Skip this step
- ✅ Set `USE_MOCK_DRUGBANK=true` in `.env` later
- ✅ No API key needed

**Option B: Get Real API Key (for Production)**
1. **Visit**: https://go.drugbank.com/
2. **Sign up** with institutional email (if available)
3. **Select**: "Academic/Research" account
4. **Wait**: 1-2 business days for approval
5. **Get key**: From https://docs.drugbank.com/v1/ after approval

---

## 📋 Checklist

Copy this to track your progress:

```
[ ] Anthropic API key obtained (REQUIRED)
[ ] Anthropic API key saved in password manager
[ ] NCBI API key obtained (optional but recommended)
[ ] NCBI API key saved in password manager
[ ] Decision on DrugBank:
    [ ] Using mock data (recommended for MVP)
    OR
    [ ] Applied for DrugBank API access
```

---

## 🔐 Where to Store Keys RIGHT NOW

**DO NOT put keys in any code file yet!**

For now, store your keys in a **secure local file** or **password manager**:

**Option 1: Password Manager (RECOMMENDED)**
- 1Password, LastPass, Bitwarden, etc.
- Create entry: "MedAssist API Keys"
- Store each key with its name

**Option 2: Secure Local File (Temporary)**
- Create a file OUTSIDE the git repo: `C:\secure\medassist-keys.txt`
- Add keys in format:
  ```
  ANTHROPIC_API_KEY=sk-ant-...
  NCBI_API_KEY=...
  ```
- **Delete this file** after copying to `.env` in US-004

---

## ✅ Verification

Once you have the Anthropic key, test it:

```bash
# Quick test with curl (replace YOUR_KEY_HERE):
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: YOUR_KEY_HERE" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-sonnet-4-20250514","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
```

Expected: JSON response with `"type": "message"`

**OR** wait for US-004 and use the verification script:
```bash
python verify_api_keys.py
```

---

## 🎯 What Happens Next (US-004)

In the next task (US-004 - Project Setup):
1. `.env` file will be created from `.env.template`
2. You'll paste your API keys into `.env`
3. Backend will be configured to load these keys
4. `verify_api_keys.py` will test all keys automatically

---

## 💰 Cost Information

| Service | Cost | What You Get |
|---------|------|--------------|
| **Anthropic** | Pay-as-you-go | $3 per 1M input tokens, $15 per 1M output tokens |
| **NCBI** | FREE | 10 req/sec with key (vs 3/sec without) |
| **DrugBank** | FREE (academic) | Drug interaction database access |

**Estimated MVP development cost**: $10-50 in Anthropic API usage

---

## 🆘 Troubleshooting

### Can't access Anthropic Console
- Try different browser or incognito mode
- Check if console.anthropic.com is accessible from your network
- Contact Anthropic support: https://support.anthropic.com/

### NCBI account issues
- Use institutional email if available for better access
- Check spam folder for verification email

### DrugBank approval taking too long
- **For MVP**: Just use mock data! Set `USE_MOCK_DRUGBANK=true`
- Academic approval usually takes 1-2 business days
- Contact: support@drugbank.com

---

## 📚 More Information

- **Detailed Guide**: See `API_KEYS_SETUP.md`
- **Status Tracking**: See `API_KEYS_OBTAINED.md`
- **Environment Template**: See `.env.template`

---

## ⚡ TL;DR

1. Get Anthropic key: https://console.anthropic.com/ → API Keys → Create
2. Save key in password manager
3. (Optional) Get NCBI key: https://www.ncbi.nlm.nih.gov/account/
4. (Optional) DrugBank: Use mock data for MVP
5. Wait for US-004 to set up `.env` file
6. Done! 🎉

---

**Next Task**: US-004 will set up the project structure and create `.env` file where you'll paste these keys.
