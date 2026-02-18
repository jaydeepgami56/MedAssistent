# API Keys Setup Guide

This guide will help you obtain all necessary API keys for the MedAssist AI project.

## Required API Keys

### 1. Anthropic API Key (REQUIRED)

**Purpose**: Powers Claude API used by all agents for clinical reasoning and NLP

**How to Obtain**:
1. Visit https://console.anthropic.com/
2. Sign up or log in to your Anthropic account
3. Navigate to API Keys section
4. Click "Create Key" or "Get API Key"
5. Copy the API key (starts with `sk-ant-...`)
6. Store it in the `.env` file as `ANTHROPIC_API_KEY`

**Testing**:
```bash
# Test the API key with a simple curl command:
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: YOUR_API_KEY_HERE" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

**Cost**: Pay-as-you-go pricing. Claude Sonnet 4 pricing available at https://www.anthropic.com/pricing

---

### 2. NCBI API Key (OPTIONAL for MVP, RECOMMENDED for production)

**Purpose**: PubMed searches by Research Agent. Increases rate limit from 3/sec to 10/sec.

**How to Obtain**:
1. Visit https://www.ncbi.nlm.nih.gov/account/
2. Create an NCBI account or log in
3. Go to Account Settings
4. Navigate to the "API Key Management" section
5. Click "Create an API Key"
6. Copy the generated API key
7. Store it in the `.env` file as `NCBI_API_KEY`

**Testing**:
```bash
# Test PubMed search with API key:
curl "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=diabetes&api_key=YOUR_NCBI_KEY&retmode=json"
```

**Cost**: FREE

**Notes**:
- Without API key: 3 requests/second limit
- With API key: 10 requests/second limit
- For MVP development, can work without this key, but recommended for production

---

### 3. DrugBank API Key (OPTIONAL for MVP - can use mock data)

**Purpose**: Drug interaction lookups for Pharmacy Agent

**How to Obtain**:

**Option A: Academic/Research Access (FREE)**
1. Visit https://go.drugbank.com/
2. Click "Sign Up" and select "Academic/Research" account
3. Fill out registration form with institutional email if available
4. Once approved, go to API Documentation: https://docs.drugbank.com/v1/
5. Navigate to "Authentication" section to get your API key
6. Store it in the `.env` file as `DRUGBANK_API_KEY`

**Option B: Commercial License (PAID)**
- Contact DrugBank for commercial licensing
- Pricing varies based on usage and features

**Option C: Mock Data for MVP (RECOMMENDED for initial development)**
- Use mock drug interaction data during MVP development
- Switch to real API once institutional access is secured

**Testing** (if using real API):
```bash
# Test drug interaction lookup:
curl -H "Authorization: Bearer YOUR_DRUGBANK_KEY" \
  "https://api.drugbank.com/v1/drug-interactions?q=aspirin"
```

**Cost**:
- Academic: FREE (requires approval)
- Commercial: Contact DrugBank for pricing

**Notes**:
- DrugBank may require institutional email for academic access
- For MVP, mock data is acceptable and already planned in the architecture
- Production deployment will need real API access or institutional license

---

## Storage Instructions

### DO NOT commit API keys to git!

1. Create a `.env` file in the project root (this file will be created in US-004)
2. Add the following entries:

```env
# Anthropic API Key (REQUIRED)
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here

# NCBI PubMed API Key (OPTIONAL for MVP)
NCBI_API_KEY=your-ncbi-key-here

# DrugBank API Key (OPTIONAL - can use mock data for MVP)
DRUGBANK_API_KEY=your-drugbank-key-here
```

3. Ensure `.env` is added to `.gitignore` (will be done in US-004)

### Secure Storage Checklist

- [ ] Keys stored in `.env` file (NOT committed to git)
- [ ] `.env` added to `.gitignore`
- [ ] Keys backed up in secure password manager (1Password, LastPass, etc.)
- [ ] Team members instructed to create their own `.env` files
- [ ] Production keys stored in Azure Key Vault or similar secret management service

---

## Environment Variable Verification

After setting up the `.env` file, verify environment variables are loaded:

```bash
# For development (after US-004 setup):
# The OpenClaw config already references ${ANTHROPIC_API_KEY}
# Backend .env will be loaded by FastAPI/Python-dotenv

# Test environment variable is set (after sourcing .env):
echo $ANTHROPIC_API_KEY  # Should output your key (first few characters)
```

---

## Next Steps

After obtaining all API keys:
1. Store them securely (password manager, encrypted file, etc.)
2. Wait for US-004 (Project Setup) where the `.env` file will be created
3. During US-004, populate the `.env` file with your obtained keys
4. Test API connectivity once backend is set up

---

## Security Best Practices

1. **Never commit API keys to version control**
2. **Use environment variables** for all secrets
3. **Rotate keys regularly** (at least every 90 days)
4. **Use separate keys** for development and production
5. **Monitor API usage** to detect unauthorized access
6. **Store production keys** in Azure Key Vault or similar service
7. **Limit API key permissions** to only what's needed
8. **Audit API key access** regularly

---

## Troubleshooting

### Anthropic API Key Issues
- Error "Invalid API Key": Check that key starts with `sk-ant-` and is copied correctly
- Error "Rate Limited": Check your usage at console.anthropic.com
- Error "Insufficient Credits": Add payment method at console.anthropic.com

### NCBI API Key Issues
- Rate limiting: Ensure API key is included in requests
- Invalid key: Regenerate key in NCBI account settings

### DrugBank API Issues
- 401 Unauthorized: Check API key format and authentication header
- Access denied: May need institutional approval
- Fallback: Use mock data for development

---

## Contact Information

- **Anthropic Support**: https://support.anthropic.com/
- **NCBI Support**: https://support.nlm.nih.gov/
- **DrugBank Support**: support@drugbank.com

