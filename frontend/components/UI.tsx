
import React from 'react';
import { createPortal } from 'react-dom';

export const Card: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className }) => (
  <div className={`glass border border-white/10 rounded-xl shadow-sm overflow-hidden ${className}`}>
    {children}
  </div>
);

export const Button: React.FC<{ 
  onClick?: () => void; 
  children: React.ReactNode; 
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'ghost';
  type?: 'button' | 'submit';
  disabled?: boolean;
  className?: string;
}> = ({ onClick, children, variant = 'primary', type = 'button', disabled, className }) => {
  const baseStyles = "px-4 py-2.5 rounded-lg text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[hsl(230,35%,4%)] disabled:opacity-50 disabled:cursor-not-allowed";
  
  const variants = {
    primary: "bg-[hsl(265,89%,66%)] hover:bg-[hsl(265,75%,58%)] text-white focus:ring-[hsl(265,89%,66%)]",
    secondary: "bg-white/10 hover:bg-white/20 text-white border border-white/20 focus:ring-[hsl(265,89%,66%)]",
    outline: "bg-transparent border border-white/30 text-white hover:bg-white/10 focus:ring-white/40",
    danger: "bg-red-600 hover:bg-red-700 text-white focus:ring-red-500",
    ghost: "text-white/70 hover:text-white bg-transparent px-2 py-1",
  };

  return (
    <button 
      type={type} 
      onClick={onClick} 
      disabled={disabled}
      className={`${baseStyles} ${variants[variant]} ${className}`}
    >
      {children}
    </button>
  );
};

export const Input: React.FC<{
  label: string;
  name: string;
  type?: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
  onKeyDown?: (e: React.KeyboardEvent<HTMLInputElement | HTMLSelectElement>) => void;
  error?: string;
  placeholder?: string;
  options?: { value: string; label: string }[];
  required?: boolean;
  className?: string;
  disabled?: boolean;
  readOnly?: boolean;
  min?: string;
  max?: string;
  minLength?: number;
}> = ({ label, name, type = 'text', value, onChange, onKeyDown, error, placeholder, options, required, className, disabled, readOnly, min, max, minLength }) => (
  <div className={`mb-4 min-w-0 ${className}`}>
    <label htmlFor={name} className="block text-sm font-medium text-white/90 mb-1.5">
      {label} {required && <span className="text-red-400">*</span>}
    </label>
    {options ? (
      <select
        id={name}
        name={name}
        value={value}
        onChange={onChange}
        disabled={disabled}
        className={`w-full px-4 py-2.5 bg-white/10 border rounded-lg text-white placeholder-white/50 appearance-none focus:ring-2 focus:ring-[hsl(265,89%,66%)] focus:border-[hsl(265,89%,66%)] outline-none transition-colors ${error ? 'border-red-500' : 'border-white/20'} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <option value="" className="bg-[hsl(230,30%,12%)] text-white">Select {label}</option>
        {options.map(opt => <option key={opt.value} value={opt.value} className="bg-[hsl(230,30%,12%)] text-white">{opt.label}</option>)}
      </select>
    ) : (
      <input
        id={name}
        name={name}
        type={type}
        value={value}
        onChange={onChange}
        onKeyDown={onKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        readOnly={readOnly}
        min={min}
        max={max}
        minLength={minLength}
        className={`w-full px-4 py-2.5 bg-white/10 border rounded-lg text-white placeholder-white/50 focus:ring-2 focus:ring-[hsl(265,89%,66%)] focus:border-[hsl(265,89%,66%)] outline-none transition-colors ${error ? 'border-red-500' : 'border-white/20'} ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${readOnly ? 'bg-white/5 cursor-default' : ''}`}
      />
    )}
    {error && (
      <p className="mt-1.5 text-xs text-red-400 flex items-center gap-1 ml-1">
        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
        {error}
      </p>
    )}
  </div>
);

export const LoadingOverlay: React.FC<{ message?: string }> = ({ message = "Loading..." }) => (
  <div className="fixed inset-0 bg-[hsl(230,35%,4%)]/95 z-50 flex flex-col items-center justify-center">
    <div className="relative">
      <div className="w-10 h-10 border-2 border-white/20 rounded-full"></div>
      <div className="w-10 h-10 border-2 border-t-[hsl(265,89%,66%)] rounded-full animate-spin absolute top-0 left-0"></div>
    </div>
    <p className="mt-4 text-white/80 text-sm font-medium">{message}</p>
  </div>
);

export const Modal: React.FC<{
  open: boolean;
  title?: string;
  children: React.ReactNode;
  onClose: () => void;
  className?: string;
  /** When true, clicking the backdrop does not close the modal (e.g. while submitting or showing result) */
  disableBackdropClose?: boolean;
}> = ({ open, title, children, onClose, className, disableBackdropClose = false }) => {
  if (!open) return null;
  return createPortal(
    <div className="fixed inset-0 z-[100]">
      <div className="absolute inset-0 bg-black/60" onClick={disableBackdropClose ? undefined : onClose} aria-hidden="true" />
      <div className="absolute inset-0 p-4 flex items-center justify-center pointer-events-none">
        <div className={`w-full max-w-4xl glass border border-white/10 rounded-xl shadow-lg overflow-hidden pointer-events-auto ${className || ""}`} onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
            <div className="min-w-0">
              <h2 className="text-lg font-semibold text-white truncate">{title || "Modal"}</h2>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors"
              aria-label="Close"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          {children}
        </div>
      </div>
    </div>,
    document.body
  );
};

/** Reusable error modal for auth and form errors. */
export const ErrorModal: React.FC<{
  open: boolean;
  title?: string;
  message: string;
  onClose: () => void;
  /** Optional primary action (e.g. "Go to login") — when set, shown next to OK. */
  actionLabel?: string;
  onAction?: () => void;
}> = ({ open, title = "Error", message, onClose, actionLabel, onAction }) => {
  if (!open) return null;
  return createPortal(
    <div className="fixed inset-0 z-[200]">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} aria-hidden />
      <div className="absolute inset-0 p-4 flex items-center justify-center">
        <div
          className="w-full max-w-md glass border border-red-400/30 rounded-xl shadow-lg overflow-hidden"
          role="alertdialog"
          aria-labelledby="error-modal-title"
          aria-describedby="error-modal-desc"
        >
          <div className="flex items-center gap-3 px-6 py-4 border-b border-white/10">
            <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 id="error-modal-title" className="text-lg font-semibold text-white">{title}</h2>
            <button
              type="button"
              onClick={onClose}
              className="ml-auto p-2 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors"
              aria-label="Close"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="px-6 py-4">
            <p id="error-modal-desc" className="text-white/85 leading-relaxed">{message}</p>
            <div className="mt-6 flex justify-end gap-3">
              {actionLabel && onAction && (
                <Button variant="primary" onClick={() => { onAction(); onClose(); }}>
                  {actionLabel}
                </Button>
              )}
              <Button variant="danger" onClick={onClose}>
                OK
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
};

/** Success modal for invite acceptance, property assignment, etc. */
export const SuccessModal: React.FC<{
  open: boolean;
  title?: string;
  message: string;
  onClose: () => void;
  /** Primary button label. Default "Continue" */
  buttonLabel?: string;
}> = ({ open, title = "Success", message, onClose, buttonLabel = "Continue" }) => {
  if (!open) return null;
  return createPortal(
    <div className="fixed inset-0 z-[200]">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} aria-hidden />
      <div className="absolute inset-0 p-4 flex items-center justify-center">
        <div
          className="w-full max-w-md glass border border-emerald-400/30 rounded-xl shadow-lg overflow-hidden"
          role="alertdialog"
          aria-labelledby="success-modal-title"
          aria-describedby="success-modal-desc"
        >
          <div className="flex items-center gap-3 px-6 py-4 border-b border-white/10">
            <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 id="success-modal-title" className="text-lg font-semibold text-white">{title}</h2>
          </div>
          <div className="px-6 py-4">
            <p id="success-modal-desc" className="text-white/85 leading-relaxed">{message}</p>
            <div className="mt-6 flex justify-end">
              <Button variant="primary" onClick={onClose}>
                {buttonLabel}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
};
