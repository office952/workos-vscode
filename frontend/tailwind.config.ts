import type { Config } from 'tailwindcss';
import tailwindcssAnimate from 'tailwindcss-animate';
import tailwindcssAspectRatio from '@tailwindcss/aspect-ratio';

export default {
  darkMode: ['class'],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  prefix: '',
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        '2xl': '1400px',
      },
    },
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        sidebar: {
          DEFAULT: 'hsl(var(--sidebar-background))',
          foreground: 'hsl(var(--sidebar-foreground))',
          primary: 'hsl(var(--sidebar-primary))',
          'primary-foreground': 'hsl(var(--sidebar-primary-foreground))',
          accent: 'hsl(var(--sidebar-accent))',
          'accent-foreground': 'hsl(var(--sidebar-accent-foreground))',
          border: 'hsl(var(--sidebar-border))',
          ring: 'hsl(var(--sidebar-ring))',
        },
        /* ─── WorkOS Semantic Colors ─── */
        'wo-surface': {
          app: 'hsl(var(--wo-surface-app))',
          shell: 'hsl(var(--wo-surface-shell))',
          raised: 'hsl(var(--wo-surface-raised))',
          inset: 'hsl(var(--wo-surface-inset))',
          input: 'hsl(var(--wo-surface-input))',
        },
        'wo-border': {
          subtle: 'hsl(var(--wo-border-subtle))',
          strong: 'hsl(var(--wo-border-strong))',
        },
        'wo-text': {
          primary: 'hsl(var(--wo-text-primary))',
          secondary: 'hsl(var(--wo-text-secondary))',
          muted: 'hsl(var(--wo-text-muted))',
          dim: 'hsl(var(--wo-text-dim))',
        },
        'wo-success': {
          DEFAULT: 'hsl(var(--wo-success))',
          foreground: 'hsl(var(--wo-success-foreground))',
          muted: 'hsl(var(--wo-success-muted))',
        },
        'wo-warning': {
          DEFAULT: 'hsl(var(--wo-warning))',
          foreground: 'hsl(var(--wo-warning-foreground))',
          muted: 'hsl(var(--wo-warning-muted))',
        },
        'wo-error': {
          DEFAULT: 'hsl(var(--wo-error))',
          foreground: 'hsl(var(--wo-error-foreground))',
          muted: 'hsl(var(--wo-error-muted))',
        },
        'wo-info': {
          DEFAULT: 'hsl(var(--wo-info))',
          foreground: 'hsl(var(--wo-info-foreground))',
          muted: 'hsl(var(--wo-info-muted))',
        },
        'wo-hover': 'hsl(var(--wo-hover))',
        'wo-active': 'hsl(var(--wo-active))',
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      keyframes: {
        'accordion-down': {
          from: {
            height: '0',
          },
          to: {
            height: 'var(--radix-accordion-content-height)',
          },
        },
        'accordion-up': {
          from: {
            height: 'var(--radix-accordion-content-height)',
          },
          to: {
            height: '0',
          },
        },
        'em-v2-fade-slide-up': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'em-v2-pulse-dot': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.4' },
        },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        'em-v2-fade-slide-up': 'em-v2-fade-slide-up 0.3s ease-out',
        'em-v2-pulse-dot': 'em-v2-pulse-dot 2s ease-in-out infinite',
      },
    },
  },
  plugins: [tailwindcssAnimate, tailwindcssAspectRatio],
} satisfies Config;