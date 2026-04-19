import { renderHook, act } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { useValidation } from '../../hooks/useValidation';

describe('useValidation Hook', () => {
  const schema = {
    email: (v: string) => (!v.includes('@') ? 'Invalid email' : null),
    age: (v: number) => (v < 18 ? 'Too young' : null),
  };

  it('initially has no errors', () => {
    const { result } = renderHook(() => useValidation());
    expect(result.current.errors).toEqual({});
  });

  it('identifies errors correctly', () => {
    const { result } = renderHook(() => useValidation());
    let isValid;
    act(() => {
      isValid = result.current.validate({ email: 'bad', age: 10 }, schema);
    });
    expect(isValid).toBe(false);
    expect(result.current.errors).toEqual({
      email: 'Invalid email',
      age: 'Too young',
    });
  });

  it('returns true for valid data', () => {
    const { result } = renderHook(() => useValidation());
    let isValid;
    act(() => {
      isValid = result.current.validate({ email: 'test@ee.com', age: 25 }, schema);
    });
    expect(isValid).toBe(true);
    expect(result.current.errors).toEqual({});
  });

  it('clears errors on request', () => {
    const { result } = renderHook(() => useValidation());
    act(() => {
      result.current.validate({ email: 'bad' }, { email: schema.email });
    });
    expect(result.current.errors.email).toBeDefined();
    act(() => {
      result.current.clearErrors();
    });
    expect(result.current.errors).toEqual({});
  });
});
