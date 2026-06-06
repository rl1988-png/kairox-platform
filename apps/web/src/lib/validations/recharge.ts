import { z } from 'zod';

export const createRechargeOrderSchema = z.object({
  amount: z
    .string()
    .regex(/^\d+(\.\d{1,8})?$/, 'Ungültiger Betrag')
    .refine((v) => Number(v) >= 30, 'Mindestbetrag: 30 USDT'),
  network: z.literal('TRC20'),
});

export type CreateRechargeOrderForm = z.infer<typeof createRechargeOrderSchema>;
