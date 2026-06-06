import { z } from 'zod';

export const loginSchema = z.object({
  username: z.string().min(3, 'Mindestens 3 Zeichen').max(64),
  password: z.string().min(8, 'Mindestens 8 Zeichen').max(128),
  rememberMe: z.boolean().default(false),
});

export const registerSchema = z.object({
  username: z.string().min(3, 'Mindestens 3 Zeichen').max(64),
  email: z.string().email('Ungültige E-Mail'),
  password: z.string().min(8, 'Mindestens 8 Zeichen').max(128),
  inviteCode: z.string().min(4, 'Einladungscode erforderlich').max(32),
});

export const resetRequestSchema = z.object({
  email: z.string().email('Ungültige E-Mail'),
});

export const resetConfirmSchema = z.object({
  token: z.string().min(16, 'Ungültiger Token').max(128),
  password: z.string().min(8, 'Mindestens 8 Zeichen').max(128),
});

export const rechargeSchema = z.object({
  txHash: z.string().min(10, 'Ungültiger Transaktions-Hash'),
});

export const withdrawSchema = z.object({
  amount: z.string().regex(/^\d+(\.\d{1,8})?$/, 'Ungültiger Betrag'),
  toAddress: z.string().min(30, 'Ungültige TRC20-Adresse'),
});

export const tradeStartSchema = z.object({
  amount: z.string().regex(/^\d+(\.\d{1,8})?$/, 'Ungültiger Betrag'),
});

export type LoginForm = z.infer<typeof loginSchema>;
export type RegisterForm = z.infer<typeof registerSchema>;
