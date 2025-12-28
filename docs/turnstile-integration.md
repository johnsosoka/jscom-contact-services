# Turnstile Integration Guide

Reusable documentation for integrating Cloudflare Turnstile CAPTCHA protection across multiple websites using the jscom-contact-services API.

## Overview

Cloudflare Turnstile provides invisible CAPTCHA protection with minimal user friction. This integration validates human submissions without requiring users to solve puzzles or click checkboxes in most cases.

**Why Turnstile:**
- Privacy-focused (no persistent cookies, no user tracking)
- Better user experience than traditional CAPTCHAs
- Free tier includes 1 million requests per month
- Adaptive challenge difficulty based on risk signals

**Multi-Site Support:**

This implementation supports multiple websites sharing the same contact API backend:
- sosoka.com
- johnsosoka.com
- Additional sites can be added following the process below

## Architecture

```
┌─────────────────────────────────────────┐
│  Frontend (Turnstile Widget)           │
│  - Renders widget on contact form       │
│  - Collects turnstile_token on success  │
└────────────────┬────────────────────────┘
                 │ POST /v1/contact
                 │ { turnstile_token, turnstile_site, ... }
                 ↓
┌─────────────────────────────────────────┐
│  contact-listener Lambda                │
│  - Validates token presence              │
│  - Calls validate_turnstile()           │
└────────────────┬────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────┐
│  turnstile.py Module                    │
│  - Maps site → SSM parameter path       │
│  - Retrieves site-specific secret       │
│  - Validates with Cloudflare API        │
└────────────────┬────────────────────────┘
                 │ https://challenges.cloudflare.com/
                 │ turnstile/v0/siteverify
                 ↓
┌─────────────────────────────────────────┐
│  Cloudflare API                         │
│  - Returns success: true/false          │
│  - Provides error codes if failed       │
└─────────────────────────────────────────┘
                 │
                 ↓ If valid
┌─────────────────────────────────────────┐
│  Normal contact form flow continues...  │
│  (SQS → filter → notify)                │
└─────────────────────────────────────────┘
```

**Validation Flow:**
1. Frontend renders Turnstile widget on page load
2. User completes form and triggers invisible challenge
3. Turnstile widget generates one-time-use token
4. Frontend includes `turnstile_token` and `turnstile_site` in API payload
5. Lambda validates token is present (403 if missing)
6. Lambda looks up site-specific secret from Parameter Store
7. Lambda validates token with Cloudflare API using secret
8. Lambda returns 403 if validation fails, 200 if successful
9. Token is single-use and expires after validation

## Adding a New Site

Follow these steps to add Turnstile protection to a new website:

### Step 1: Create Turnstile Widget in Cloudflare

1. Log in to Cloudflare Dashboard
2. Navigate to **Turnstile** section
3. Click **Add Site**
4. Configure widget:
   - **Site Name:** Descriptive name (e.g., "example-com contact form")
   - **Domains:** Add all domains where widget will be used (e.g., `example.com`, `www.example.com`)
   - **Widget Mode:** Managed (recommended) or Non-Interactive
   - **Pre-Clearance:** Leave disabled unless you need it
5. Click **Create**
6. Save the **Site Key** (public, goes in frontend code)
7. Save the **Secret Key** (private, goes in Parameter Store)

### Step 2: Store Secret in AWS Parameter Store

Store the Turnstile secret key in SSM Parameter Store following the naming convention:

```bash
aws ssm put-parameter \
  --name "/jscom/turnstile/example-com/secret-key" \
  --value "YOUR_SECRET_KEY_FROM_CLOUDFLARE" \
  --type "SecureString" \
  --region us-west-2 \
  --profile jscom
```

**Naming Convention:**
- Pattern: `/jscom/turnstile/{site-name}/secret-key`
- Replace dots in domain with hyphens: `example.com` → `example-com`
- Always use SecureString type for encryption at rest

### Step 3: Update Turnstile Configuration

Edit `lambdas/src/contact-listener/app/turnstile.py` and add the new site to `SITE_SECRET_MAP`:

```python
SITE_SECRET_MAP = {
    "sosoka.com": "/jscom/turnstile/sosoka-com/secret-key",
    "johnsosoka.com": "/jscom/turnstile/johnsosoka-com/secret-key",
    "example.com": "/jscom/turnstile/example-com/secret-key",  # New site
}
```

**Important:** The key must match the `turnstile_site` value sent from the frontend.

### Step 4: Verify Terraform IAM Permissions

The Lambda IAM policy already grants wildcard access to all Turnstile parameters:

```hcl
# In terraform/lambdas.tf
{
  Effect   = "Allow"
  Action   = ["ssm:GetParameter"]
  Resource = "arn:aws:ssm:us-west-2:*:parameter/jscom/turnstile/*"
}
```

No Terraform changes needed unless you modify the parameter path structure.

### Step 5: Deploy Changes

Deploy the updated configuration:

```bash
cd terraform
export AWS_PROFILE=jscom
terraform apply
```

### Step 6: Integrate Widget in Frontend

See **Frontend Integration Examples** section below for platform-specific implementation.

## Parameter Store Convention

All Turnstile secrets follow a consistent naming structure for easy management:

**Path Structure:**
```
/jscom/turnstile/{site-name}/secret-key
```

**Current Sites:**

| Site | Parameter Path |
|------|----------------|
| sosoka.com | `/jscom/turnstile/sosoka-com/secret-key` |
| johnsosoka.com | `/jscom/turnstile/johnsosoka-com/secret-key` |

**Listing All Secrets:**

```bash
aws ssm get-parameters-by-path \
  --path "/jscom/turnstile" \
  --recursive \
  --region us-west-2 \
  --profile jscom
```

**Updating a Secret:**

```bash
aws ssm put-parameter \
  --name "/jscom/turnstile/sosoka-com/secret-key" \
  --value "NEW_SECRET_KEY" \
  --type "SecureString" \
  --overwrite \
  --region us-west-2 \
  --profile jscom
```

## Frontend Integration Examples

### Next.js (React)

Install the Turnstile React component:

```bash
npm install @marsidev/react-turnstile
```

**Component Implementation:**

```typescript
import { useState } from 'react';
import { Turnstile } from '@marsidev/react-turnstile';

export default function ContactForm() {
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!turnstileToken) {
      alert('Please complete security verification');
      return;
    }

    setIsSubmitting(true);

    const payload = {
      contact_name: 'John Doe',
      contact_email: 'john@example.com',
      contact_message: 'Test message',
      turnstile_token: turnstileToken,
      turnstile_site: 'example.com'  // Must match SITE_SECRET_MAP key
    };

    try {
      const response = await fetch('https://api.johnsosoka.com/v1/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        alert('Message sent successfully!');
      } else {
        const error = await response.json();
        alert(`Error: ${error.error}`);
      }
    } catch (err) {
      console.error('Submission error:', err);
      alert('Failed to send message');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Your form fields here */}

      <Turnstile
        siteKey="YOUR_SITE_KEY"
        onSuccess={(token) => setTurnstileToken(token)}
        onError={() => setTurnstileToken(null)}
        onExpire={() => setTurnstileToken(null)}
      />

      <button type="submit" disabled={!turnstileToken || isSubmitting}>
        {isSubmitting ? 'Sending...' : 'Send Message'}
      </button>
    </form>
  );
}
```

**Key Points:**
- Widget automatically renders and challenges user
- Token is single-use and expires
- Disable submit button until token is available
- Reset token on error or expiration
- Token must be included in every API request

### Jekyll (Static Site with jQuery)

**HTML Template:**

```html
<!-- Include Cloudflare Turnstile script in <head> or before closing </body> -->
<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>

<form id="contact-form">
  <input type="text" name="contact_name" placeholder="Name" required>
  <input type="email" name="contact_email" placeholder="Email" required>
  <textarea name="contact_message" placeholder="Message" required></textarea>

  <!-- Turnstile widget container -->
  <div class="cf-turnstile"
       data-sitekey="{{ site.turnstile.site_key }}"
       data-callback="onTurnstileSuccess"
       data-error-callback="onTurnstileError"
       data-expired-callback="onTurnstileExpired">
  </div>

  <button type="submit" id="submit-btn">Send Message</button>
</form>
```

**JavaScript Implementation:**

```javascript
let turnstileToken = null;

// Callback when Turnstile challenge succeeds
function onTurnstileSuccess(token) {
  turnstileToken = token;
  $('#submit-btn').prop('disabled', false);
}

function onTurnstileError() {
  turnstileToken = null;
  $('#submit-btn').prop('disabled', true);
  alert('Security verification failed. Please refresh the page.');
}

function onTurnstileExpired() {
  turnstileToken = null;
  $('#submit-btn').prop('disabled', true);
}

$(document).ready(function() {
  // Disable submit until Turnstile token is available
  $('#submit-btn').prop('disabled', true);

  $('#contact-form').on('submit', function(e) {
    e.preventDefault();

    if (!turnstileToken) {
      alert('Please complete security verification');
      return;
    }

    const formData = {
      contact_name: $('input[name="contact_name"]').val(),
      contact_email: $('input[name="contact_email"]').val(),
      contact_message: $('textarea[name="contact_message"]').val(),
      turnstile_token: turnstileToken,
      turnstile_site: 'example.com'  // Must match SITE_SECRET_MAP key
    };

    $.ajax({
      url: 'https://api.johnsosoka.com/v1/contact',
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(formData),
      success: function(response) {
        alert('Message sent successfully!');
        $('#contact-form')[0].reset();
        turnstileToken = null;
        // Turnstile will auto-reset after successful submission
      },
      error: function(xhr) {
        const error = xhr.responseJSON?.error || 'Failed to send message';
        alert('Error: ' + error);
      }
    });
  });
});
```

**Jekyll Configuration (_config.yml):**

```yaml
turnstile:
  site_key: "YOUR_SITE_KEY"
```

### HTML/Vanilla JavaScript

**Minimal Implementation:**

```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
</head>
<body>
  <form id="contact-form">
    <input type="text" id="name" required>
    <input type="email" id="email" required>
    <textarea id="message" required></textarea>

    <div class="cf-turnstile"
         data-sitekey="YOUR_SITE_KEY"
         data-callback="onSuccess">
    </div>

    <button type="submit" id="submit-btn" disabled>Send</button>
  </form>

  <script>
    let turnstileToken = null;

    function onSuccess(token) {
      turnstileToken = token;
      document.getElementById('submit-btn').disabled = false;
    }

    document.getElementById('contact-form').addEventListener('submit', async (e) => {
      e.preventDefault();

      const payload = {
        contact_name: document.getElementById('name').value,
        contact_email: document.getElementById('email').value,
        contact_message: document.getElementById('message').value,
        turnstile_token: turnstileToken,
        turnstile_site: 'example.com'
      };

      const response = await fetch('https://api.johnsosoka.com/v1/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        alert('Success!');
      } else {
        alert('Failed');
      }
    });
  </script>
</body>
</html>
```

## Testing with Cloudflare Test Keys

Cloudflare provides test keys that always pass validation for local development:

**Test Site Key (always passes):**
```
1x00000000000000000000AA
```

**Test Secret Key (always passes):**
```
1x0000000000000000000000000000000AA
```

**Local Development Setup:**

```bash
# Store test secret in Parameter Store
aws ssm put-parameter \
  --name "/jscom/turnstile/localhost/secret-key" \
  --value "1x0000000000000000000000000000000AA" \
  --type "SecureString" \
  --region us-west-2 \
  --profile jscom

# Add to turnstile.py SITE_SECRET_MAP
"localhost": "/jscom/turnstile/localhost/secret-key"
```

**Frontend Test Configuration:**

```javascript
// Use test site key in development
const SITE_KEY = process.env.NODE_ENV === 'development'
  ? '1x00000000000000000000AA'
  : 'YOUR_PRODUCTION_SITE_KEY';

<Turnstile
  siteKey={SITE_KEY}
  onSuccess={(token) => setTurnstileToken(token)}
/>

// Include in payload
turnstile_site: process.env.NODE_ENV === 'development' ? 'localhost' : 'example.com'
```

**Important Testing Notes:**
- Test keys bypass all verification (always return success)
- Tokens from test keys are still single-use
- Test widget appears and functions identically to production
- Always test with production keys before deploying

## Troubleshooting

### Widget Not Rendering

**Symptoms:** Turnstile widget container is empty or shows error

**Causes & Solutions:**

1. **Script not loaded:**
   - Verify `<script src="https://challenges.cloudflare.com/turnstile/v0/api.js">` is present
   - Check browser console for script loading errors
   - Ensure `async defer` attributes are set

2. **Invalid site key:**
   - Verify site key matches Cloudflare Dashboard
   - Check for typos or whitespace in data-sitekey attribute

3. **Domain not allowed:**
   - Add current domain to allowed domains in Cloudflare Dashboard
   - Include both www and non-www versions if needed
   - For localhost, use test keys or add localhost to allowed domains

4. **CSP (Content Security Policy) blocking:**
   - Add `https://challenges.cloudflare.com` to script-src
   - Add `https://challenges.cloudflare.com` to frame-src

### 403 Error: "Security verification required"

**Cause:** `turnstile_token` is missing from request payload

**Solution:**
- Verify widget is rendering correctly
- Check that `onSuccess` callback is setting token variable
- Ensure token variable is included in fetch/AJAX payload
- Verify form submission isn't bypassing token check

**Debug Steps:**

```javascript
// Add logging before submission
console.log('Turnstile token:', turnstileToken);
if (!turnstileToken) {
  console.error('Token is null or undefined');
  return;
}
```

### 403 Error: "Security verification failed"

**Cause:** Token validation failed with Cloudflare API

**Common Reasons:**

1. **Wrong site key used:**
   - Verify frontend site key matches Cloudflare Dashboard
   - Ensure you're not mixing test and production keys

2. **Token already used:**
   - Tokens are single-use only
   - Widget auto-refreshes after failed submission
   - Don't retry with same token

3. **Token expired:**
   - Tokens expire after 5 minutes
   - Widget will auto-reset and generate new token

4. **Wrong site parameter:**
   - Verify `turnstile_site` matches a key in `SITE_SECRET_MAP`
   - Check for typos: `sosoka.com` not `www.sosoka.com`

5. **Wrong secret key in Parameter Store:**
   - Verify secret key in SSM matches Cloudflare Dashboard
   - Check for copy-paste errors or extra whitespace

**Debug Steps:**

```bash
# Check Lambda logs for detailed error
aws logs tail /aws/lambda/contact-listener --follow --profile jscom

# Verify Parameter Store secret
aws ssm get-parameter \
  --name "/jscom/turnstile/example-com/secret-key" \
  --with-decryption \
  --region us-west-2 \
  --profile jscom
```

### Widget Showing "Verify you are human"

**Cause:** Turnstile detected suspicious behavior

**Normal Behavior:**
- Turnstile is adaptive and may show interactive challenge
- More likely on VPNs, shared IPs, or suspicious user agents
- Challenge difficulty increases with risk signals

**Solutions:**
- User completes interactive challenge
- Widget mode set to "Managed" (recommended) in Cloudflare Dashboard
- Not an error - just more visible verification

### Lambda Timeout or Network Error

**Symptoms:** Contact form hangs or shows generic error

**Causes:**

1. **Cloudflare API unreachable:**
   - Check Lambda has internet access (NAT Gateway if in VPC)
   - Verify security groups allow outbound HTTPS

2. **SSM Parameter Store error:**
   - Check Lambda IAM policy has `ssm:GetParameter` permission
   - Verify parameter path exists and is correct

3. **Request timeout:**
   - Default timeout in `turnstile.py` is 5 seconds
   - Check CloudWatch logs for timeout errors

**Debug Steps:**

```bash
# Check Lambda CloudWatch logs
aws logs tail /aws/lambda/contact-listener --since 10m --profile jscom

# Test Lambda IAM permissions
aws lambda invoke \
  --function-name contact-listener \
  --payload '{"body": "{}"}' \
  /tmp/response.json \
  --profile jscom
```

### Error Codes from Cloudflare API

When validation fails, Cloudflare returns error codes in the response:

| Error Code | Meaning | Solution |
|------------|---------|----------|
| `missing-input-secret` | Secret key not provided | Check Parameter Store path |
| `invalid-input-secret` | Secret key is invalid | Verify secret matches Dashboard |
| `missing-input-response` | Token not provided | Include turnstile_token in payload |
| `invalid-input-response` | Token is invalid or expired | Generate new token |
| `timeout-or-duplicate` | Token already used | Use fresh token for retry |
| `internal-error` | Cloudflare API error | Retry request |

**Viewing Error Codes:**

Lambda logs error codes when validation fails:

```
Turnstile validation failed: ['invalid-input-response'], IP: 192.168.1.100
```

## Security Considerations

### Token Handling

**Never trust frontend validation:**
- Always validate tokens server-side
- Tokens are single-use and expire after validation
- Never log or store tokens (not needed after validation)

**Token Lifecycle:**
1. Widget generates token after challenge completion
2. Frontend sends token to API (one-time use)
3. Lambda validates with Cloudflare API
4. Token becomes invalid after validation
5. Widget automatically generates new token for next submission

### Secret Key Management

**Best Practices:**
- Store secrets in AWS Parameter Store (SecureString type)
- Never commit secrets to version control
- Use separate secrets for each site
- Rotate secrets periodically
- Limit IAM access to Parameter Store

**Rotation Process:**

```bash
# Generate new secret in Cloudflare Dashboard
# Update Parameter Store
aws ssm put-parameter \
  --name "/jscom/turnstile/example-com/secret-key" \
  --value "NEW_SECRET_KEY" \
  --type "SecureString" \
  --overwrite \
  --region us-west-2 \
  --profile jscom

# No Lambda redeployment needed (secret fetched on each request)
```

### Rate Limiting

Turnstile provides rate limiting at the Cloudflare level:
- Protects against automated abuse
- Adaptive challenge difficulty based on risk
- No additional rate limiting needed in Lambda

### Monitoring

**CloudWatch Metrics to Monitor:**
- Lambda invocation errors
- Turnstile validation failure rate
- API Gateway 403 response rate

**CloudWatch Log Insights Query:**

```
# Count Turnstile validation failures by IP
fields @timestamp, @message
| filter @message like /Turnstile validation failed/
| stats count() by @message
```

## API Reference

### Request Payload

All contact form submissions must include Turnstile fields:

```json
{
  "contact_name": "John Doe",
  "contact_email": "john@example.com",
  "contact_message": "Hello, this is a test message.",
  "turnstile_token": "0.Abc123...",
  "turnstile_site": "example.com"
}
```

**Required Fields:**
- `contact_message` (string): Message content
- `turnstile_token` (string): One-time token from Turnstile widget
- `turnstile_site` (string): Site domain matching SITE_SECRET_MAP key

**Optional Fields:**
- `contact_name` (string): Sender name
- `contact_email` (string): Sender email
- `consulting_contact` (boolean): Set to true for consulting form type
- `company_name` (string): Required if consulting_contact is true
- `industry` (string): Required if consulting_contact is true

### Response Codes

**200 OK:**
```json
{
  "message": "Message Received. Currently Processing"
}
```

**400 Bad Request (missing required field):**
```json
{
  "error": "contact_message is a required field"
}
```

**403 Forbidden (token missing):**
```json
{
  "error": "Security verification required"
}
```

**403 Forbidden (validation failed):**
```json
{
  "error": "Security verification failed"
}
```

## Implementation Checklist

Use this checklist when adding Turnstile to a new site:

### Backend Setup
- [ ] Create Turnstile widget in Cloudflare Dashboard
- [ ] Save Site Key and Secret Key
- [ ] Store secret in Parameter Store: `/jscom/turnstile/{site-name}/secret-key`
- [ ] Add site to `SITE_SECRET_MAP` in `turnstile.py`
- [ ] Deploy Lambda changes via Terraform
- [ ] Verify Lambda has SSM permissions (already configured)

### Frontend Setup
- [ ] Install Turnstile library or add script tag
- [ ] Add widget container to contact form
- [ ] Configure widget with site key
- [ ] Implement success/error callbacks
- [ ] Disable submit button until token available
- [ ] Include `turnstile_token` in API payload
- [ ] Include `turnstile_site` in API payload
- [ ] Test form submission end-to-end

### Testing
- [ ] Test with production keys on staging site
- [ ] Verify 403 response when token is missing
- [ ] Verify 403 response when token is invalid
- [ ] Verify 200 response on successful submission
- [ ] Test token expiration (wait 5+ minutes before submit)
- [ ] Test error handling (network failures, etc.)
- [ ] Check CloudWatch logs for validation errors
- [ ] Verify Turnstile widget renders correctly
- [ ] Test on multiple browsers/devices

### Documentation
- [ ] Update site-specific documentation with site key
- [ ] Document any custom frontend implementations
- [ ] Add site to this guide's "Current Sites" table

## Additional Resources

**Cloudflare Turnstile Documentation:**
- [Official Docs](https://developers.cloudflare.com/turnstile/)
- [Client-side rendering](https://developers.cloudflare.com/turnstile/get-started/client-side-rendering/)
- [Server-side validation](https://developers.cloudflare.com/turnstile/get-started/server-side-validation/)

**Turnstile Libraries:**
- [@marsidev/react-turnstile](https://www.npmjs.com/package/@marsidev/react-turnstile) (React)
- [Official JavaScript API](https://developers.cloudflare.com/turnstile/reference/client-side-rendering/)

**jscom-contact-services:**
- [Repository](https://github.com/johnsosoka/jscom-contact-services)
- [CLAUDE.md](../CLAUDE.md) - Developer guidance
- [README.md](../README.md) - Project overview
