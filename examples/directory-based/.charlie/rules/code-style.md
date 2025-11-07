---
title: "Code Style Guidelines"
description: "Standards for code formatting and best practices"
order: 2
alwaysApply: false
globs:
  - "**/*.py"
  - "**/*.ts"
  - "**/*.js"
  - "!**/test_*.py"
  - "!**/*.test.ts"
priority: "high"
categories:
  - style
  - formatting
---

## Python Style

- Use **Black** for formatting (line length: 100)
- Use **type hints** for all function parameters and return types
- Follow **PEP 8** conventions
- Use **docstrings** for all public functions and classes

Example:
```python
def calculate_total(items: List[Item]) -> Decimal:
    """Calculate total price including tax.
    
    Args:
        items: List of items to calculate
        
    Returns:
        Total price with tax applied
    """
    subtotal = sum(item.price for item in items)
    return subtotal * Decimal("1.08")
```

## TypeScript Style

- Use **Prettier** for formatting
- Enable **strict mode** in tsconfig.json
- Prefer **const** over **let**
- Use **explicit types** (avoid 'any')
- Use **interfaces** for object shapes

Example:
```typescript
interface UserProfile {
  id: string;
  name: string;
  email: string;
  createdAt: Date;
}

const fetchUserProfile = async (userId: string): Promise<UserProfile> => {
  const response = await api.get(`/users/${userId}`);
  return response.data;
};
```

