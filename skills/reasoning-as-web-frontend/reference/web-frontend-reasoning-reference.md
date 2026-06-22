# Web-frontend surface reasoning — reference for `reasoning-as-web-frontend`

> Progressive-disclosure Level 3 (loaded on demand). Worked output example, edge-case/failure handling, common pitfalls, decision trees, and deep domain guidance. SKILL.md is the operational reasoning contract.

## Pages & Components
- [Page name] (component tree, key interactions)
- [Page name] (component tree, key interactions)

## State Management
- [Context/Store name]: what state, why, scope
- [Context/Store name]: what state, why, scope

## API Contracts
- METHOD /path → request shape → response shape
- Include error scenarios and status codes

## Performance Budget
- Core Web Vitals targets
- Bundle size target
- Key optimization opportunities

## Accessibility
- WCAG compliance level target
- Critical keyboard interactions
- Screen reader requirements
- Mobile/touch considerations

## Dependencies
- What backend APIs must exist
- What design patterns are assumed
- What third-party libraries anticipated

## Risks & Questions
- Blockers or unclear requirements
- High-effort features to clarify
- Assumptions that need validation

---
Ready for: Council negotiation
```

## Example Application

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

## Common Pitfalls

Avoid these patterns when reasoning about web frontend:

1. **Assuming state updates are instant** - React state and async operations are unpredictable. Optimistic updates can conflict with server truth. Always track loading/error states separately and validate after async completion.
   - Counter: Implement proper loading states, debounce rapid changes, use server-side validation as source of truth.

2. **Over-engineering state management** - Not every piece of state needs Redux/Zustand. Simple component state works fine for most cases. Only elevate to global state when multiple unrelated components need it.
   - Counter: Start with local state, only lift when needed. Document your state "why" (why is it at this level?).

3. **Ignoring localStorage persistence implications** - Persisting to localStorage works until it doesn't (storage limits, stale data after backend changes, cross-tab sync failures). Don't persist without a clear expiry or validation strategy.
   - Counter: Persist with timestamps, validate on app startup, provide clear user messaging when syncing with server.

4. **API contract mismatches discovered late** - Frontend assumes response fields that backend doesn't provide. Only caught in integration testing or production.
   - Counter: Define API contracts explicitly in PRD analysis. Frontend/backend teams sign off together. Use shared TypeScript types where possible.

5. **Form state complexity without plan** - Nested objects, conditional fields, dynamic arrays lead to bugs. State gets out of sync with validation. Form submission fails silently.
   - Counter: Use dedicated form libraries (React Hook Form, Formik). Define validation schema upfront. Test form state separately from submission.

6. **Race conditions in async state** - User clicks twice, triggers two async calls. The second response arrives first, gets overwritten by the first. UI shows wrong data.
   - Counter: Cancel in-flight requests before new ones. Use Request IDs to ignore stale responses. Show loading state to prevent double-clicks.

7. **Cross-component communication via prop drilling** - Passing props 4-5 levels deep becomes unmaintainable. Changes to props break multiple components. Siblings can't communicate easily.
   - Counter: Use context for shared concerns (auth, theme, feature flags). Use state management for domain state. Keep props for local concerns only.

## State Management Decision Tree

When analyzing a PRD, use this decision tree to choose your state management approach:

```
START: Do multiple unrelated components need this state?
  NO  → Keep in component (useState at lowest common ancestor)
        → When: Local form state, UI toggles, temporary filters
        → Example: Modal open/close, tab selection, accordion expansion

  YES → Will state persist across page reloads?
    NO  → Use React Context + useReducer (ephemeral shared state)
          → When: Auth user info, theme selection, feature flags
          → Example: User context with login/logout, theme switcher
          → Trade-off: Simpler than Redux, no persistence, re-renders on change

    YES → How much state and how often does it change?
      SMALL + INFREQUENT  → localStorage + Context
                            → When: User preferences (theme, language, sidebar collapse)
                            → Example: Persisting theme choice, saved filters
                            → Trade-off: Simple, works offline, risk of stale data

      LARGE + FREQUENT    → Zustand or similar lightweight store
                            → When: Domain state (products, cart, user posts)
                            → Example: Shopping cart, feed data, editing state
                            → Trade-off: More powerful than context, less boilerplate than Redux
                            
      COMPLEX + FREQUENT  → Redux or similar with middleware
                            → When: Time-travel debugging needed, complex flows (undo/redo)
                            → Example: Collaborative editor, complex workflow with multiple steps
                            → Trade-off: Most powerful, most boilerplate, best for debugging

      ASYNC + PAGINATED   → React Query / SWR + lightweight store
                            → When: Server-driven data (API responses, cache invalidation)
                            → Example: User feed, search results, data tables
                            → Trade-off: Handles caching/syncing for you, opinionated
```

### Persistence Strategy Checklist

When deciding to persist state to localStorage:

- **What to persist:** User preferences (theme, layout), saved form drafts, UI state (sidebar open/closed)
- **What NOT to persist:** Auth tokens (use httpOnly cookies), sensitive data, frequently-changing server data
- **Validation on startup:** Always validate persisted data against current API/schema. Discard if stale (check timestamp).
- **Sync strategy:** On app mount, compare localStorage with server state. Show spinner while syncing. Disable UI if conflict detected.
- **Storage limits:** localStorage is ~5-10MB. Monitor size for large state. Compress if needed.

### Backend Sync Points

Identify where state must sync with backend:

| State | Sync Trigger | Conflict Resolution |
|-------|--------------|---------------------|
| Auth token | Login/logout | Server truth (token validation) |
| User profile | Edit profile form submit | Optimistic update + rollback on error |
| Shopping cart | Add/remove item | Merge server cart with local changes |
| Feature flags | App startup | Server truth always, client cache for perf |
| Saved filters | Save button click | Server persists, local cache for speed |

## Edge Cases & Handling Strategies

### Edge Case 1: State Synchronization Conflicts (Optimistic Updates vs Server Truth)

**Scenario:** User edits a form field, you update local state immediately (optimistic). Meanwhile, server validation fails or another user modified the same resource. Server returns conflict error.

**Action - Graceful Handling:**
```javascript
// Example: Optimistic form update with rollback
const [formData, setFormData] = useState(initialData);
const [isSaving, setIsSaving] = useState(false);
const [error, setError] = useState(null);

const handleFieldChange = async (field, value) => {
  // Optimistic update
  setFormData(prev => ({ ...prev, [field]: value }));
  setIsSaving(true);
  
  try {
    const response = await api.updateForm({ [field]: value });
    // Server confirms - we're good
    setFormData(response.data);
    setError(null);
  } catch (err) {
    // Conflict: rollback to server state
    if (err.status === 409) {
      setFormData(err.conflictingData); // Fetch server version
      setError('Your changes conflicted. Showing server version.');
    } else {
      setError(err.message);
    }
  } finally {
    setIsSaving(false);
  }
};
```

**Escalation Path:**
- **Flag as blocker** if: Multiple concurrent edits expected (shared document). Requires collaborative merge strategy.
- **Alert Council** if: Conflict resolution logic differs from backend expectations. Needs explicit PRD guidance.
- **Proceed normally** if: Single-user editing or last-write-wins acceptable.

---

### Edge Case 2: Complex Form State with Nested Objects and Validation

**Scenario:** User fills a form with nested address object, dynamic line items array, conditional fields (show shipping if not local pickup). Validation errors on 3 nested fields. How do you track and display all states?

**Action - Graceful Handling:**
```javascript
// Example: Form state with nested validation using React Hook Form
import { useForm, useFieldArray, Controller } from 'react-hook-form';

function OrderForm() {
  const { control, watch, formState: { errors }, handleSubmit } = useForm({
    defaultValues: {
      customer: { name: '', email: '' },
      items: [{ sku: '', qty: 1 }],
      shipping: { method: 'standard' },
      address: { street: '', city: '', zip: '' }
    },
    mode: 'onChange' // Validate as user types
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'items'
  });

  const shippingMethod = watch('shipping.method');

  const onSubmit = (data) => {
    console.log('Form data:', data);
    // Send to API
    api.saveOrder(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* Nested customer section */}
      <Controller
        name="customer.name"
        control={control}
        rules={{ required: 'Name required' }}
        render={({ field, fieldState: { error } }) => (
          <div>
            <input {...field} placeholder="Name" />
            {error && <span className="error">{error.message}</span>}
          </div>
        )}
      />

      {/* Dynamic items array */}
      {fields.map((item, idx) => (
        <div key={item.id}>
          <Controller
            name={`items.${idx}.qty`}
            control={control}
            rules={{ min: 1 }}
            render={({ field, fieldState: { error } }) => (
              <div>
                <input {...field} type="number" />
                {error && <span className="error">{error.message}</span>}
              </div>
            )}
          />
          <button type="button" onClick={() => remove(idx)}>Remove</button>
        </div>
      ))}

      {/* Conditional field based on watch */}
      {shippingMethod === 'standard' && (
        <Controller
          name="address.zip"
          control={control}
          rules={{ required: 'ZIP required for standard shipping' }}
          render={({ field, fieldState: { error } }) => (
            <div>
              <input {...field} placeholder="ZIP" />
              {error && <span className="error">{error.message}</span>}
            </div>
          )}
        />
      )}
    </form>
  );
}
```

**Escalation Path:**
- **Flag as blocker** if: Form has 20+ fields or 5+ levels of nesting. Requires UX/design review to simplify.
- **Alert Council** if: Validation rules change server-side post-submit. Needs explicit versioning strategy.
- **Proceed normally** if: Using established form library (React Hook Form, Formik). Clear schema exists.

---

### Edge Case 3: Cross-Component State Sharing (Sibling Communication)

**Scenario:** ProductList component filters products. SidebarFilter component lets users change filters. They're siblings, not parent-child. How do they communicate state without prop drilling?

**Action - Graceful Handling:**
```javascript
// Example: Context-based filter sharing
const FilterContext = createContext();

export function FilterProvider({ children }) {
  const [filters, setFilters] = useState({ category: null, priceRange: [0, 1000] });
  const [results, setResults] = useState([]);

  const updateFilters = useCallback((newFilters) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
    // Fetch new results based on filters
    fetchResults(newFilters).then(setResults);
  }, []);

  return (
    <FilterContext.Provider value={{ filters, updateFilters, results }}>
      {children}
    </FilterContext.Provider>
  );
}

function SidebarFilter() {
  const { filters, updateFilters } = useContext(FilterContext);
  return (
    <select onChange={(e) => updateFilters({ category: e.target.value })}>
      {/* Options */}
    </select>
  );
}

function ProductList() {
  const { results } = useContext(FilterContext);
  return <div>{results.map(p => ...)}</div>;
}

// Root layout
function App() {
  return (
    <FilterProvider>
      <div className="layout">
        <SidebarFilter />
        <ProductList />
      </div>
    </FilterProvider>
  );
}
```

**Escalation Path:**
- **Flag as blocker** if: Sibling communication pattern repeated across 5+ feature areas. Needs centralized state management.
- **Alert Council** if: Filter changes trigger expensive computations (sorting, ML ranking). Needs debounce/caching strategy.
- **Proceed normally** if: Filters are simple (1-3 categories), results load quickly, isolated feature area.

---

### Edge Case 4: Performance Degradation Under Large Datasets in State

**Scenario:** User searches products. Results are 5,000 items. Storing all in state causes re-renders to slow down. Filtering/sorting becomes janky. Scrolling stutters.

**Action - Graceful Handling:**
```javascript
// Example: Pagination + virtualization for large lists
import { FixedSizeList as List } from 'react-window';
import { useCallback } from 'react';

function ProductListLarge({ totalCount }) {
  const pageSize = 50;
  const [page, setPage] = useState(0);
  const [items, setItems] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Only fetch current page, not all items
  const loadPage = useCallback(async (pageNum) => {
    setIsLoading(true);
    const data = await api.getProducts({
      offset: pageNum * pageSize,
      limit: pageSize
    });
    setItems(data);
    setIsLoading(false);
  }, []);

  // Virtualize: render only visible items
  const Row = ({ index, style }) => {
    const pageOffset = page * pageSize;
    const actualIndex = index - pageOffset;
    const item = items[actualIndex];
    
    if (actualIndex < 0 || actualIndex >= items.length) {
      return <div style={style} className="product-card">Loading...</div>;
    }
    
    return <div style={style} className="product-card">{item?.name}</div>;
  };

  return (
    <div>
      <List
        height={600}
        itemCount={totalCount}
        itemSize={80}
        width="100%"
      >
        {Row}
      </List>
      <button onClick={() => loadPage(page + 1)} disabled={isLoading}>
        Load More
      </button>
    </div>
  );
}
```

**Escalation Path:**
- **Flag as blocker** if: Dataset is 50,000+ items AND virtualization alone isn't enough (need both pagination + virtualization). Requires backend search index (Elasticsearch).
- **Alert Council** if: Performance target is <100ms filtering. May need backend search index (Elasticsearch) or advanced client-side optimization.
- **Proceed normally** if: Dataset <10,000 and pagination is acceptable OR virtualization with proper index mapping covers the need. Virtualization handles rendering performance; pagination handles data loading efficiency. Use both for very large datasets.

---

### Edge Case 5: Race Conditions in Async State Updates

**Scenario:** User clicks "Save" button twice rapidly. Two async requests fire. The second request completes first (faster network path). Local state updates. Then the first request completes, overwriting with stale data.

**Action - Graceful Handling:**
```javascript
// Example: Race condition prevention with abort controller + request IDs
function useAsyncState(initialValue) {
  const [data, setData] = useState(initialValue);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const requestIdRef = useRef(0);

  const setAsyncData = useCallback(async (asyncFn) => {
    const currentId = ++requestIdRef.current;
    setIsLoading(true);
    setError(null);

    try {
      const result = await asyncFn();
      // Only update if this request is still the latest
      if (currentId === requestIdRef.current) {
        setData(result);
      }
    } catch (err) {
      if (currentId === requestIdRef.current) {
        setError(err);
      }
    } finally {
      if (currentId === requestIdRef.current) {
        setIsLoading(false);
      }
    }
  }, []);

  return { data, error, isLoading, setAsyncData };
}

function SaveableForm() {
  const { data, error, isLoading, setAsyncData } = useAsyncState({});

  const handleSave = async () => {
    await setAsyncData(() => api.saveForm(data));
  };

  return (
    <>
      <button onClick={handleSave} disabled={isLoading}>
        {isLoading ? 'Saving...' : 'Save'}
      </button>
      {error && <span>Error: {error.message}</span>}
    </>
  );
}
```

**Escalation Path:**
- **Flag as blocker** if: Same data being saved from multiple sources (auto-save + manual save). Needs explicit conflict resolution.
- **Alert Council** if: Race condition happens frequently in user testing. May indicate UX issue (button should be disabled while loading).
- **Proceed normally** if: Button is disabled during async operation (prevents double-click), or last-write-wins acceptable.

---

### Edge Case 6: localStorage Data Staleness Causing Inconsistency

**Scenario:** User sets theme to dark in one tab. localStorage persists it. User closes that tab, opens app in new tab. localStorage loads dark theme. But server says user prefers light (profile update in another browser). App loads with conflicting state.

**Action - Graceful Handling:**
```javascript
// Example: Validate localStorage against server on app startup
function usePersistedState(key, defaultValue) {
  const [state, setState] = useState(() => {
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : defaultValue;
  });

  // On mount, validate with server
  useEffect(() => {
    const validateWithServer = async () => {
      try {
        const serverValue = await api.getUserPreference(key);
        const localValue = JSON.parse(localStorage.getItem(key));

        if (serverValue !== localValue) {
          // Conflict detected
          setState(serverValue); // Server wins
          localStorage.setItem(key, JSON.stringify(serverValue));
          console.warn(`Restored ${key} from server (was ${localValue})`);
        }
      } catch (err) {
        // Server unreachable, use local
        console.log(`Using local ${key}, server unreachable`);
      }
    };

    validateWithServer();
  }, [key]);

  const updateState = (newValue) => {
    setState(newValue);
    localStorage.setItem(key, JSON.stringify(newValue));
  };

  return [state, updateState];
}
```

**Escalation Path:**
- **Flag as blocker** if: Stale data causes incorrect behavior (e.g., user privacy setting). Requires immediate server-fetch on app load.
- **Alert Council** if: Validation conflicts happen frequently. May indicate lack of sync mechanism or unclear API contract.
- **Proceed normally** if: Stale data is benign (theme preference), user can manually refresh.

