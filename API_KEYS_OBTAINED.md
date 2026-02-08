# API Keys Obtained - Status Checklist

This file tracks which API keys have been obtained for the MedAssist AI project.

**IMPORTANT**: This file should NOT contain actual API keys, only status tracking.
Actual keys should be stored in `.env` file (which is git-ignored).

## Status Legend
- ✅ Obtained and verified working
- ⏳ In progress / waiting for approval
- ❌ Not yet started
- 🔄 Optional (can use mock data for MVP)

---

## API Keys Status

### 1. Anthropic API Key (REQUIRED)
**Status**: ❌ Not yet obtained

**Instructions**:
1. Visit https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Create new API key
5. Copy key (starts with `sk-ant-...`)
6. Store in `.env` file as `ANTHROPIC_API_KEY=sk-ant-...`
7. Test using `python verify_api_keys.py`

**Verification**:
- [ ] API key obtained
- [ ] Stored in `.env` file
- [ ] Backed up in password manager
- [ ] Tested with `verify_api_keys.py`
- [ ] Can make successful API calls

**Notes**:
- Cost: Pay-as-you-go (see https://www.anthropic.com/pricing)
- Model: claude-sonnet-4-20250514
- Used by: All agents for clinical reasoning

---

### 2. NCBI/PubMed API Key (OPTIONAL for MVP, RECOMMENDED for production)
**Status**: ❌ Not yet obtained

**Instructions**:
1. Visit https://www.ncbi.nlm.nih.gov/account/
2. Create NCBI account or log in
3. Go to Account Settings → API Key Management
4. Click "Create an API Key"
5. Copy the generated key
6. Store in `.env` file as `NCBI_API_KEY=...`
7. Test using `python verify_api_keys.py`

**Verification**:
- [ ] API key obtained
- [ ] Stored in `.env` file
- [ ] Backed up in password manager
- [ ] Tested with `verify_api_keys.py`
- [ ] Can make PubMed search requests

**Notes**:
- Cost: FREE
- Benefit: Increases rate limit from 3/sec to 10/sec
- Used by: Research Agent for PubMed literature searches
- Can work without this key for MVP (reduced rate limit)

---

### 3. DrugBank API Key (OPTIONAL - can use mock data for MVP)
**Status**: 🔄 Can use mock data for MVP

**Instructions**:

**Option A: Academic/Research Access (FREE)**
1. Visit https://go.drugbank.com/
2. Sign up with institutional/academic email
3. Select "Academic/Research" account type
4. Wait for approval (may take 1-2 business days)
5. Once approved, visit https://docs.drugbank.com/v1/
6. Navigate to Authentication section
7. Copy your API key
8. Store in `.env` file as `DRUGBANK_API_KEY=...`

**Option B: Use Mock Data (RECOMMENDED for MVP)**
1. Set `USE_MOCK_DRUGBANK=true` in `.env` file
2. Mock drug interaction data will be used during development
3. Switch to real API later once access is secured

**Verification**:
- [ ] Decision made: Real API or Mock Data
- [ ] If Real API:
  - [ ] API key obtained
  - [ ] Stored in `.env` file
  - [ ] Backed up in password manager
- [ ] If Mock Data:
  - [ ] `USE_MOCK_DRUGBANK=true` set in `.env`
  - [ ] Mock data implementation planned

**Notes**:
- Cost: FREE for academic, paid for commercial
- Used by: Pharmacy Agent for drug interaction checks
- Mock data is acceptable for MVP and testing
- Production may require institutional license

---

## Environment Variable Configuration

After obtaining API keys, your `.env` file should look like this:

```env
# Required
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here

# Optional (recommended for production)
NCBI_API_KEY=your-ncbi-key-here

# Optional (or use mock data)
DRUGBANK_API_KEY=your-drugbank-key-here
# OR
USE_MOCK_DRUGBANK=true
```

---

## Security Checklist

- [ ] `.env` file created (copy from `.env.template`)
- [ ] All obtained API keys added to `.env`
- [ ] `.env` file is in `.gitignore` (verified)
- [ ] API keys backed up in secure password manager
- [ ] API keys NOT committed to git (double-check with `git status`)
- [ ] Team members instructed to obtain their own keys
- [ ] Production keys will use separate environment/key vault

---

## Verification Steps

### After obtaining Anthropic API key:

```bash
# Install dependencies if not already installed
pip install requests python-dotenv

# Run verification script
python verify_api_keys.py
```

Expected output:
```
✓ Anthropic API key is VALID and working!
✓ All REQUIRED API keys are configured and working!
```

### Manual verification (alternative):

```bash
# Test Anthropic API key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: YOUR_ANTHROPIC_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 10,
    "messages": [{"role": "user", "content": "Hi"}]
  }'
```

---

## Next Steps

1. ✅ Complete this checklist by obtaining all required API keys
2. ✅ Store keys in `.env` file (will be created in US-004)
3. ✅ Run `python verify_api_keys.py` to verify all keys
4. ⏳ Wait for US-004 (Project Setup) to set up backend with .env loading
5. ⏳ Test API integration once backend is running

---

## Troubleshooting

### "API key not found" error
- Ensure `.env` file is in project root: `C:\Dev\openclaw\.env`
- Ensure `python-dotenv` is installed: `pip install python-dotenv`
- Check that environment variables are loaded in your application

### Anthropic API returns 401 Unauthorized
- Verify key starts with `sk-ant-`
- Check for extra spaces or quotes in `.env` file
- Regenerate key at https://console.anthropic.com/ if needed

### NCBI API rate limiting
- Verify API key is being sent with requests
- Check that key is valid in NCBI account settings

### DrugBank access denied
- Academic accounts require approval (1-2 days)
- Ensure you're using institutional email if requesting academic access
- Consider using mock data for development

---

## Resources

- **Anthropic Console**: https://console.anthropic.com/
- **Anthropic Pricing**: https://www.anthropic.com/pricing
- **Anthropic Documentation**: https://docs.anthropic.com/
- **NCBI Account**: https://www.ncbi.nlm.nih.gov/account/
- **PubMed API Docs**: https://www.ncbi.nlm.nih.gov/books/NBK25501/
- **DrugBank**: https://go.drugbank.com/
- **DrugBank API Docs**: https://docs.drugbank.com/v1/

---

## Security Contacts

If you suspect API key compromise:
1. **Immediately revoke** the compromised key
2. **Generate new key** at the respective service console
3. **Update `.env` file** with new key
4. **Notify team** if shared environment
5. **Audit logs** to check for unauthorized usage

---

Last Updated: 2026-02-08
Updated By: System Setup
