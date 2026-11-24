import React from 'react';
import type { Meta, StoryObj } from '@storybook/react-vite';
import { MaintenanceDisclosure } from './MaintenanceDisclosure';

const meta = {
  title: 'Maintenance/Disclosure',
  component: MaintenanceDisclosure,
  tags: ['autodocs'],
} satisfies Meta<typeof MaintenanceDisclosure>;

export default meta;

/** Example for a building issue that needs immediate attention. */
export const WithEscalation: StoryObj<typeof meta> = {
  args: {
    label: 'When should I call maintenance?',
    children: 'Call dispatch if there is standing water.',
  },
};
