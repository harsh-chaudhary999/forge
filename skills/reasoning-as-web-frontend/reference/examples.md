# Example Application — Worked Web Perspective Output

**Input PRD:** "Add 2FA (two-factor authentication) to user accounts"

**Web Perspective Output:**

```markdown
# Web Frontend Perspective: 2FA Feature

## Pages & Components

- **Login Page**
  - EmailInput (component)
  - PasswordInput (component)
  - LoginButton (component)
  - 2FA Option Toggle (show 2FA setup?)
  - ErrorDisplay (component)

- **2FA Setup Page**
  - PhoneInput (with validation)
  - QRCodeDisplay (for authenticator apps)
  - ManualKeyDisplay (fallback)
  - VerificationCodeInput (user confirms code works)
  - RecoveryCodesDisplay (with copy/download options)
  - ConfirmButton

- **2FA Verify Page**
  - CodeInput (6-digit code)
  - ResendButton (SMS resend)
  - AlternateMethod Link (try backup method)
  - SubmitButton
  - RememberThisDevice Checkbox

- **Settings Page - 2FA Management**
  - ActiveDevices List (authenticator app, SMS, backup codes)
  - RemoveDevice Button (per device)
  - RecoveryCodesViewer (display, regenerate)
  - BackupMethodSelector

## State Management

```javascript
// Auth Context
{
  user: {
    id,
    email,
    twoFaEnabled: boolean,
    twoFaMethods: ['authenticator-app', 'sms']
  },
  isAuthenticated: boolean,
  twoFaVerified: boolean, // only after 2FA verification
  token: string
}

// 2FA Setup Context (ephemeral, cleared after setup)
{
  setupStep: 'choose-method' | 'configure' | 'verify' | 'backup-codes',
  selectedMethod: 'authenticator-app' | 'sms',
  phoneNumber: string,
  qrCode: string,
  secret: string,
  recoveryCodesGenerated: string[],
  verificationCode: string,
  error: string | null,
  loading: boolean
}
```

## API Contracts

- **POST /auth/2fa/enable** (start 2FA setup)
  - Request: `{ method: 'authenticator-app' | 'sms', phone?: string }`
  - Response: `{ secret: string, qr_url: string, recovery_codes: string[] }`
  - Errors: `{ code: 'invalid_method' | 'invalid_phone', message: string }`

- **POST /auth/2fa/verify-setup** (confirm 2FA works)
  - Request: `{ setup_id: string, code: string }`
  - Response: `{ success: boolean, message: string }`
  - Errors: `{ code: 'invalid_code' | 'expired', message: string }`

- **POST /auth/login** (with 2FA)
  - Request: `{ email: string, password: string }`
  - Response if 2FA required: `{ requires_2fa: true, session_token: string }`
  - Errors: `{ code: 'invalid_credentials', message: string }`

- **POST /auth/2fa/verify-login** (during login)
  - Request: `{ session_token: string, code: string, remember_device?: boolean }`
  - Response: `{ success: boolean, access_token: string, refresh_token?: string }`
  - Errors: `{ code: 'invalid_code' | 'expired', message: string }`

- **GET /user/2fa/devices**
  - Response: `{ devices: [{ id, type: 'authenticator-app' | 'sms', identifier: string, added_at: timestamp }] }`

- **DELETE /user/2fa/devices/:id**
  - Response: `{ success: boolean }`
  - Errors: `{ code: 'cannot_remove_last_device', message: string }`

## Performance Budget

- Login page initial load: <1.5s (no user data, simple form)
- 2FA setup page: <1.5s (QR code is SVG, not image)
- 2FA verification step: <500ms (just validation, no page reload)
- 2FA setup modal (if in settings): <800ms
- Component bundle impact: <15KB gzipped (new components only)

**Optimizations:**
- QR code generation client-side (qrcode.react)
- Recovery codes in textarea with copy-to-clipboard
- Lazy load 2FA management UI (only if authenticated and 2FA enabled)

## Accessibility

- **WCAG 2.2 AA** - All 2FA flows must pass automated + manual audit
- **Keyboard Navigation:**
  - Tab through all code inputs without mouse
  - Enter submits verification code
  - Escape closes dialogs
  - Visible focus indicators (blue outline, 2px)
- **Screen Reader Support:**
  - "Code input, 6 digits required" aria-label
  - Error messages announced as alert role
  - Recovery codes list with list semantics
  - Status updates via aria-live
- **Color Contrast:**
  - Code input focus: 4.5:1 (text on background)
  - Error messages: 4.5:1 (red text on background)
- **Mobile/Touch:**
  - 44x44px minimum button size
  - Numeric keyboard for code input (inputmode="numeric")
  - SMS input triggers phone keyboard (inputmode="tel")
- **Forms:**
  - Phone field required indicator (visual + aria-required)
  - Validation errors linked to inputs (aria-describedby)
  - Success messages announced

## Dependencies

- **Backend APIs:** All 6 endpoints listed above must exist and be documented
- **Design tokens:** Colors for focus states, error states, success states
- **Third-party:** qrcode.react (for QR code generation, ~3KB)
- **Auth flow:** Must support session tokens + access tokens

## Risks & Questions

1. **High:** SMS delivery latency - what timeout for code entry? 5 min? 10 min?
2. **High:** Recovery codes - should users regenerate them? When?
3. **Medium:** Backup methods - user adds SMS after authenticator app? Which is primary?
4. **Medium:** "Remember this device" - how long? 30 days? Need cookie strategy?
5. **Low:** QR code accessibility - how do users without camera input secret manually?

---
Ready for: Council negotiation
```
