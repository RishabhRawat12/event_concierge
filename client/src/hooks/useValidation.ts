import { useState, useCallback } from 'react';

interface ValidationError {
  [key: string]: string;
}

export const useValidation = () => {
  const [errors, setErrors] = useState<ValidationError>({});

  const validate = useCallback((data: any, schema: Record<string, (val: any) => string | null>) => {
    const newErrors: ValidationError = {};
    let isValid = true;

    Object.keys(schema).forEach((field) => {
      const error = schema[field](data[field]);
      if (error) {
        newErrors[field] = error;
        isValid = false;
      }
    });

    setErrors(newErrors);
    return isValid;
  }, []);

  const clearErrors = useCallback(() => setErrors({}), []);

  return { errors, validate, clearErrors };
};
