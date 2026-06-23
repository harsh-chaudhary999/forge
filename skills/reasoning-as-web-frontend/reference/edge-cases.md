# Edge Cases & Handling Strategies

## Edge Case 1: State Synchronization Conflicts (Optimistic Updates vs Server Truth)

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

## Edge Case 2: Complex Form State with Nested Objects and Validation

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

## Edge Case 3: Cross-Component State Sharing (Sibling Communication)

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

## Edge Case 4: Performance Degradation Under Large Datasets in State

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

## Edge Case 5: Race Conditions in Async State Updates

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

## Edge Case 6: localStorage Data Staleness Causing Inconsistency

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
