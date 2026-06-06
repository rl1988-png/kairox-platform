export type NavItem = {
  href: string;
  label: string;
  labelKey?: string;
  /** Paths that mark this item active (defaults to href) */
  matchPaths?: string[];
  /** Center elevated tab (Trade on kairox.cc) */
  center?: boolean;
};

export type SubNavItem = {
  href: string;
  label: string;
  labelKey?: string;
  exact?: boolean;
};

/** kairox.cc bottom bar: Home · Wallet · Trade · Team · Mine */
export const bottomNavItems: NavItem[] = [
  { href: '/home', label: 'Home', labelKey: 'nav.home' },
  {
    href: '/wallet',
    label: 'Wallet',
    labelKey: 'nav.wallet',
    matchPaths: ['/wallet', '/wallet/bill', '/wallet/bind', '/recharge', '/withdraw'],
  },
  { href: '/trade', label: 'Trade', labelKey: 'nav.trade', center: true },
  {
    href: '/team',
    label: 'Team',
    labelKey: 'nav.team',
    matchPaths: ['/team', '/team/list'],
  },
  {
    href: '/account',
    label: 'Mein',
    labelKey: 'nav.mine',
    matchPaths: ['/account', '/account/invite', '/reset-password'],
  },
];

/** Desktop sidebar — same core tabs as kairox.cc */
export const mainNavItems: NavItem[] = bottomNavItems.filter((item) => !item.center);

/** Insert Trade after Wallet in sidebar (no center styling) */
export const sidebarNavItems: NavItem[] = [
  bottomNavItems[0],
  bottomNavItems[1],
  { ...bottomNavItems[2], center: false },
  bottomNavItems[3],
  bottomNavItems[4],
];

export const sidebarExtraItems: NavItem[] = [
  { href: '/recharge', label: 'Recharge', labelKey: 'nav.recharge' },
  { href: '/withdraw', label: 'Withdraw', labelKey: 'nav.withdraw' },
  { href: '/wallet/bill', label: 'Bill', labelKey: 'nav.bill' },
  { href: '/wallet/bind', label: 'Bind address', labelKey: 'nav.bindAddress' },
  { href: '/team/list', label: 'Team stats', labelKey: 'nav.teamStats' },
  { href: '/account/invite', label: 'Invite & QR', labelKey: 'nav.invite' },
];

export const walletSubNav: SubNavItem[] = [
  { href: '/wallet', label: 'Balance', labelKey: 'nav.walletBalance', exact: true },
  { href: '/recharge', label: 'Recharge', labelKey: 'nav.recharge' },
  { href: '/withdraw', label: 'Withdraw', labelKey: 'nav.withdraw', exact: true },
  { href: '/wallet/bill', label: 'Bill', labelKey: 'nav.bill' },
  { href: '/wallet/bind', label: 'Address', labelKey: 'nav.bindAddress' },
];

export const teamSubNav: SubNavItem[] = [
  { href: '/team', label: 'My team', labelKey: 'nav.myTeam', exact: true },
  { href: '/team/list', label: 'Statistics', labelKey: 'nav.teamStats' },
  { href: '/account/invite', label: 'Invite', labelKey: 'nav.invite' },
];

export const accountSubNav: SubNavItem[] = [
  { href: '/account', label: 'Profile', labelKey: 'nav.profile', exact: true },
  { href: '/account/invite', label: 'Invite & QR', labelKey: 'nav.invite' },
  { href: '/reset-password', label: 'Password', labelKey: 'nav.password' },
];

export function isNavActive(pathname: string, item: NavItem): boolean {
  const paths = item.matchPaths ?? [item.href];
  return paths.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}

export function isSubNavActive(pathname: string, tab: SubNavItem): boolean {
  if (tab.exact) return pathname === tab.href;
  return pathname === tab.href || pathname.startsWith(`${tab.href}/`);
}

export function navItemForPath(pathname: string): NavItem | undefined {
  return bottomNavItems.find((item) => isNavActive(pathname, item));
}
