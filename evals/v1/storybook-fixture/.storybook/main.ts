import type { StorybookConfig } from '@storybook/react-vite';

const config: StorybookConfig = {
  framework: '@storybook/react-vite',
  stories: ['../*.stories.tsx'],
  addons: ['@storybook/addon-mcp'],
  features: { componentsManifest: true },
};

export default config;
