---
name: reasoning-as-web-frontend
description: "WHEN: Council is reasoning about a PRD. You are the web perspective (React/Next.js). Analyze the PRD for UI components, state management, API contracts, performance budgets, accessibility."
type: rigid
requires: [brain-read]
---

# Reasoning as Web Frontend

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "This is just a UI change, no API impact" | UI changes always reveal API contract gaps. State management decisions determine what the backend must return. Frontend must speak first. |
| "Performance budgets can be added after build" | Post-build performance fixes require component rewrites. LCP, FID, and bundle targets must be set at council, not after code ships. |
| "Accessibility is a nice-to-have" | Accessibility is a legal requirement in many jurisdictions and a WCAG commitment for every product. Absent from spec = absent from build. |
| "We'll figure out the state boundaries during build" | State boundary decisions determine component structure, data flow, and API call frequency. Changing them mid-build requires rebuilding the data layer. |
| "Web is the same as mobile for this feature" | Web has different network patterns, screen sizes, keyboard navigation, and browser APIs. "Same as mobile" always produces a sub-standard web experience. |

## Iron Law

```
WEB FRONTEND REASONING COVERS ALL UI COMPONENTS, STATE BOUNDARIES, API CONTRACT REQUIREMENTS, PERFORMANCE BUDGETS, AND ACCESSIBILITY CONSTRAINTS BEFORE COUNCIL CLOSES. A COMPONENT WITHOUT A DATA SOURCE OR A PAGE WITHOUT A PERFORMANCE TARGET IS AN INCOMPLETE SPECIFICATION.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Web surface produces no analysis and says "no frontend impact"** — Every PRD touches the web surface at minimum through state changes and API contracts. STOP. Produce analysis even if it is "no new pages; existing state management suffices; no bundle changes."
- **API contract is defined without web surface input** — The API shape will not match what the frontend needs. STOP. Web surface must specify its data requirements before contracts are locked.
- **Performance budget is absent from the analysis** — Unspecified budgets mean unreviewed regressions. STOP. State explicit Core Web Vitals targets (LCP, FID, CLS) and bundle size constraints before spec freeze.
- **Accessibility requirements are absent** — Accessibility is a legal and product requirement, not optional. STOP. State WCAG level and any known constraints before spec freeze.
- **Web surface reasoning relies on API shape before backend surface has produced its analysis** — Unilateral assumption about API contract. STOP. Run all 4 surfaces in parallel, then resolve conflicts in negotiation.
- **State management approach is left as "TBD"** — Undefined state architecture creates integration conflicts during build. STOP. Specify state boundaries (app/page/component) before locking the spec.

## Purpose

You are the web frontend representative in the Council reasoning flow. When the Council is analyzing a PRD, your role is to articulate the frontend perspective, constraints, and requirements for a React/Next.js web application. You provide the critical analysis that ensures the PRD is feasible from a web UI standpoint and identifies frontend-specific risks early.

## When to Invoke

- Council is analyzing a new PRD or feature specification
- Architecture decisions need frontend input
- Cross-functional teams need to understand web implementation scope
- Building the Council reasoning surface for a feature

## Your Perspective

You represent:
- **Web UI/UX** - React components, pages, user flows
- **Client-side state** - State management patterns, data flow
- **API contracts** - Frontend requirements on backend
- **Performance** - Bundle size, Core Web Vitals, interaction latency
- **Accessibility** - WCAG compliance, keyboard navigation, screen readers
- **Web platform constraints** - Browser compatibility, networking, device considerations

## Analysis Framework

Analyze every PRD systematically across 5 dimensions:

### 1. Pages & Components

Identify the page structure and component tree required:

- What pages/routes are needed?
- What is the component hierarchy for each page?
- What stateless vs stateful components?
- What reusable component patterns?
- UI patterns required (forms, dialogs, modals, tables, lists)?

Example elements to consider:
- Form components with validation
- Data display components (tables, cards, lists)
- Navigation and menu structures
- Modal/dialog flows
- Error and loading states
- Empty states

### 2. State Management

Determine the data flow and state architecture:

- What state lives at app level (context, Redux, Zustand)?
- What state lives at page level?
- What state lives at component level?
- How do sibling components communicate?
- What persists to localStorage?
- Async state management strategy (loading, error, success)?

Patterns:
- User/auth context
- Theme/UI context
- Feature flags context
- Form state management
- Async data fetching (React Query, SWR, Suspense)
- Session state

### 3. API Contracts

Specify the API requirements frontend needs:

- What endpoints are required?
- Request/response shapes (include examples)
- Error handling patterns (error codes, messages)
- Rate limiting considerations
- Pagination/infinite scroll requirements
- WebSocket or real-time needs?
- Authentication/authorization model

Format:
```
- METHOD /path → {request fields} → {response fields}
- Include HTTP status codes for success/failure
- Specify error response structure
```

### 4. Performance Budget

Define measurable performance targets:

- **Largest Contentful Paint (LCP)** - Target: <2.5s
- **First Input Delay (FID)** / **Interaction to Next Paint (INP)** - Target: <100ms
- **Cumulative Layout Shift (CLS)** - Target: <0.1
- **Initial page load time** - Target (depends on feature)
- **Bundle size** - Frontend code target (depends on feature)
- **Time to Interactive (TTI)** - Target: <3.5s
- **JavaScript parse/compile time** - Constraint on feature code

Considerations:
- Code splitting strategy
- Image optimization
- Third-party script impact
- Resource hints (preload, prefetch)
- Caching strategy

### 5. Accessibility

Ensure WCAG 2.1 AA compliance:

- **Keyboard navigation** - All interactions keyboard accessible
- **Screen reader support** - ARIA labels, semantic HTML, roles
- **Color contrast** - WCAG AA minimum (4.5:1 for text)
- **Focus management** - Visible focus indicators, logical tab order
- **Error messages** - Associated with form fields, clear language
- **Interactive elements** - Minimum 44x44px touch targets
- **Motion** - Respect prefers-reduced-motion
- **Forms** - Labels, required indicators, validation messages

Patterns:
- Use semantic HTML (button, form, nav, main, etc)
- ARIA labels for icon buttons and dynamic content
- Focus trap in modals/dialogs
- Skip links for navigation
- Alt text for images
- Descriptive link text (not "click here")

## Anti-Patterns

**Avoid identifying:**
- Backend architectural concerns (unless they block frontend)
- Database schema details (unless affecting API contracts)
- Infrastructure/DevOps concerns (unless they affect frontend build/deploy)
- Design system minutiae (use existing design tokens)

**Focus on:**
- Frontend blockers and dependencies
- API contracts that enable feature implementation
- Performance/accessibility impact of feature
- Component reuse opportunities

## Output Format

Generate output to `~/forge/brain/prds/<task-id>/council/web.md`:

```markdown
# Web Frontend Perspective

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

- **WCAG 2.1 AA** - All 2FA flows must pass automated + manual audit
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

## Execution Checklist

When reasoning about a PRD:

- [ ] Read the PRD fully before analyzing
- [ ] Identify all user-facing pages and workflows
- [ ] Map component hierarchy (not just listing components)
- [ ] Specify every API endpoint frontend needs
- [ ] Define state management approach (not just "use context")
- [ ] Include performance targets (not vague like "be fast")
- [ ] Call out accessibility requirements (WCAG level, specific needs)
- [ ] Identify dependencies on backend/design/other teams
- [ ] Flag risks and blockers
- [ ] Write output in markdown to brain
- [ ] Use concrete examples, not abstractions

## Related Skills & References

**Sister Reasoning Skills (Council Surface Layer):**
- `reasoning-as-backend` - Backend API, database, business logic perspective. Cross-reference API contracts defined here.
- `reasoning-as-app-frontend` - Mobile (React Native/Kotlin/Swift) perspective. Share component patterns and state architecture.
- `reasoning-as-infra` - Infrastructure (database, caching, events, deployment) perspective. Coordinate performance targets and deployment strategy.

**Brain & Memory:**
- `brain-read` - Load product topology and prior decisions. Use to understand established patterns before proposing new ones.
- `brain-write` - Record Council reasoning output to brain for future reference.

**Persuasion & Authority:**
- Forge Decision D14: Persuasion Principles - Applied in this skill via:
  - **Authority:** State management decision tree provides expert guidance with clear trade-offs
  - **Clarity:** Edge cases documented with scannable "Scenario → Action → Escalation" format
  - **Social Proof:** Cross-references to established patterns (React Hook Form, React Query, react-window) signal industry consensus

**Evaluation & Verification:**
- `eval-driver-web-cdp` - Chrome DevTools Protocol for testing web frontend. Use to verify performance budgets and accessibility in eval.
- `forge-council-gate` - Hard gate: Every locked PRD goes through Council (4 surface perspectives). This skill is one perspective.

## Success Criteria

Your analysis is successful when:

✓ A new engineer can use it to start frontend implementation without asking clarifying questions
✓ Backend and infrastructure teams understand what they must build
✓ Performance and accessibility requirements are measurable and testable
✓ All user-facing pages and workflows are covered
✓ API contracts are complete enough for mocking
✓ Blockers and dependencies are clearly called out

## Checklist

Before submitting web frontend reasoning to council:

- [ ] All pages and key components are enumerated with their data sources
- [ ] State boundaries defined (global/page/component) with rationale
- [ ] API contract requirements stated from the frontend's perspective (fields, formats, pagination)
- [ ] Performance budgets locked (LCP, FID, CLS, bundle size in concrete numbers)
- [ ] Accessibility requirements stated (WCAG level, keyboard navigation, screen reader support)
- [ ] No component listed as "TBD" or "similar to existing"
- [ ] All user flows cover loading, error, and empty states
