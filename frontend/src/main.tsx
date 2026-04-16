import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { Toaster } from 'react-hot-toast';
import { LoaderProvider } from './services/loader.tsx';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <LoaderProvider>
      <App />
      <Toaster
        position="bottom-right"
        containerClassName="w-full inset-x-0 p-4"
        toastOptions={{
          duration: 3500,
          className: 'flex items-center justify-center',
          style: {
            fontSize: '15px',
            width: '100%',
            maxWidth: '400px',
            textAlign: 'center',
            padding: '12px 20px',
            borderRadius: '8px',
            boxShadow: '0 4px 10px rgba(0, 0, 0, 0.1)',
            color: '#333',
            background: '#fff',
          },
          // Custom styles for different types of toasts
          success: {
            style: {
              background: '#d4edda',
              color: '#155724',
              border: '1px solid #c3e6cb',
            },
          },
          error: {
            style: {
              background: '#f8d7da',
              color: '#721c24',
              border: '1px solid #f5c6cb',
            },
          },
        }}
      />
    </LoaderProvider>
  </StrictMode>
);
