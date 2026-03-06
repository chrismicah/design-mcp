"""
Build REAL, actionable data for the MCP.
This creates:
1. Component code registry (actual TSX source from shadcn/ui)
2. Behavioral templates for every page type
3. Semantic token sets
4. Accessibility guidelines per component
5. Enriches ALL patterns with this data
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PATTERNS_PATH = BASE_DIR / "data" / "patterns.json"

# ============================================================
# 1. BEHAVIORAL TEMPLATES — What patterns DO, not just how they look
# ============================================================
BEHAVIORAL_TEMPLATES = {
    "Dashboard": {
        "behavioral_description": (
            "Dashboard loads with skeleton placeholders matching final layout. "
            "Stats cards animate in with staggered fade. Charts lazy-load after above-fold content. "
            "Sidebar collapses to icons on mobile with hamburger toggle. "
            "Date range picker filters all widgets simultaneously. "
            "Real-time data updates via polling/websocket without full page refresh. "
            "Empty widgets show contextual CTAs to configure data sources."
        ),
        "accessibility_notes": (
            "Requires ARIA landmarks: nav for sidebar, main for content area, complementary for widgets. "
            "Charts must have aria-label describing the trend. Data tables need proper th/td structure with scope. "
            "All interactive elements need visible focus indicators (2px ring). "
            "Color-coded status indicators must also have text/icon alternatives. "
            "Keyboard: Tab navigates widgets, Enter/Space activates, Escape closes dropdowns."
        ),
    },
    "Landing Page": {
        "behavioral_description": (
            "Hero section loads instantly with above-fold content prioritized. "
            "Scroll-triggered animations for feature sections (intersection observer). "
            "CTA buttons have hover states with subtle scale/shadow transitions. "
            "Social proof section auto-rotates testimonials with pause on hover. "
            "Pricing toggle switches between monthly/annual with animated price change. "
            "Mobile: hamburger nav, stacked sections, full-width CTAs. "
            "Footer has newsletter signup with inline validation."
        ),
        "accessibility_notes": (
            "Hero heading must be h1, sections use h2. Skip-to-content link at top. "
            "Auto-rotating carousels must have pause control and aria-live='polite'. "
            "CTA buttons need descriptive text (not just 'Click here'). "
            "Decorative images use aria-hidden='true', meaningful images need alt text. "
            "Color contrast: all text meets WCAG AA (4.5:1 normal, 3:1 large). "
            "Reduced motion: respect prefers-reduced-motion for animations."
        ),
    },
    "E-commerce": {
        "behavioral_description": (
            "Product grid loads with skeleton cards. Filters update results without page reload. "
            "Add-to-cart shows micro-animation (icon bounce, count update). "
            "Product images support zoom on hover, swipe gallery on mobile. "
            "Price displays with strike-through for discounts. "
            "Out-of-stock items show 'Notify me' instead of add-to-cart. "
            "Cart persists across sessions via localStorage/cookies. "
            "Quick-view modal shows key details without leaving the listing."
        ),
        "accessibility_notes": (
            "Product cards need descriptive labels: 'Product Name, $Price, Rating'. "
            "Image galleries need keyboard navigation (left/right arrows). "
            "Add-to-cart button announces success via aria-live region. "
            "Filters use fieldset/legend grouping. Price ranges use aria-valuemin/max. "
            "Sort dropdown uses native select or combobox pattern with ARIA. "
            "Focus management: after adding to cart, focus stays on product."
        ),
    },
    "Auth": {
        "behavioral_description": (
            "Form validates email format on blur, password strength on keyup. "
            "Submit button disables during API call with loading spinner. "
            "Error messages appear inline below each field with red border. "
            "Social login buttons (Google, GitHub) above email form with 'or' divider. "
            "Password field has show/hide toggle. "
            "Remember me checkbox persists email. "
            "Successful login redirects to previous page or dashboard. "
            "Failed login shakes form subtly, shows error toast."
        ),
        "accessibility_notes": (
            "Every input needs a visible label (not just placeholder). "
            "Error messages linked via aria-describedby to their input. "
            "Password visibility toggle needs aria-label ('Show password'/'Hide password'). "
            "Form uses aria-invalid='true' on error fields. "
            "Submit button announces loading state. "
            "Social login buttons need descriptive labels ('Sign in with Google')."
        ),
    },
    "Settings": {
        "behavioral_description": (
            "Settings organized in tabbed sections or sidebar navigation. "
            "Changes save automatically (optimistic UI) or via explicit Save button. "
            "Destructive actions (delete account) require confirmation modal with typed confirmation. "
            "Toggle switches for boolean settings with instant visual feedback. "
            "Form sections collapsible on mobile. "
            "Unsaved changes trigger 'Leave without saving?' prompt on navigation."
        ),
        "accessibility_notes": (
            "Tabs use ARIA tab pattern: role='tablist', role='tab', aria-selected. "
            "Toggle switches need aria-checked and descriptive labels. "
            "Confirmation modals trap focus and return focus on close. "
            "Destructive buttons use aria-describedby linking to warning text. "
            "Save confirmation uses aria-live to announce success/failure."
        ),
    },
    "Chat": {
        "behavioral_description": (
            "Messages load in reverse chronological order, scroll to bottom on new message. "
            "Typing indicator shows when other user is composing. "
            "Message input auto-resizes with content. Send on Enter, newline on Shift+Enter. "
            "Unread messages show count badge on channel. "
            "Image/file attachments show preview before sending. "
            "Message actions (reply, edit, delete) appear on hover/long-press. "
            "Timestamps group messages by day."
        ),
        "accessibility_notes": (
            "Message list uses role='log' with aria-live='polite' for new messages. "
            "Each message needs aria-label with sender, time, and content. "
            "Typing indicator uses aria-live='assertive'. "
            "Send button needs aria-label. Attachment upload needs accessible file picker. "
            "Keyboard: Enter sends, Tab navigates, Escape cancels reply."
        ),
    },
    "Pricing": {
        "behavioral_description": (
            "Plans displayed in 2-4 column grid with 'Popular' badge on recommended plan. "
            "Monthly/annual toggle with percentage savings shown. "
            "Feature comparison table expandable below cards. "
            "CTA buttons change text per tier ('Start Free', 'Upgrade', 'Contact Sales'). "
            "Enterprise tier shows 'Contact us' instead of price. "
            "FAQ accordion below pricing cards. "
            "Hover state lifts card with shadow."
        ),
        "accessibility_notes": (
            "Pricing cards use heading hierarchy (h2 for plan name). "
            "Feature lists use proper list elements. "
            "Toggle uses switch role with aria-checked. "
            "Comparison table uses proper th/td with scope. "
            "Popular badge uses aria-label ('Recommended plan'). "
            "CTA buttons describe action ('Start free trial for Starter plan')."
        ),
    },
    "Portfolio": {
        "behavioral_description": (
            "Project grid with hover overlay showing title and category. "
            "Lightbox or detail page on click with full case study. "
            "Filter by category/tag with animated transitions. "
            "Lazy-loaded images with blur-up placeholder. "
            "About section with bio, skills, and contact CTA. "
            "Smooth scroll between sections."
        ),
        "accessibility_notes": (
            "Project images need descriptive alt text. "
            "Lightbox traps focus and closes on Escape. "
            "Filter buttons use aria-pressed for active state. "
            "Smooth scroll respects prefers-reduced-motion. "
            "Contact form follows standard accessible form patterns."
        ),
    },
    "Admin Panel": {
        "behavioral_description": (
            "Data table with sortable columns, inline search, and bulk actions. "
            "Row selection via checkbox with Select All in header. "
            "Pagination with page size selector. "
            "Create/Edit forms in slide-over panel or modal. "
            "Delete requires confirmation. Bulk delete shows count. "
            "Status badges with color + text (not color alone). "
            "Export to CSV/PDF from toolbar."
        ),
        "accessibility_notes": (
            "Data table: proper th scope, aria-sort on sortable columns. "
            "Checkbox column: aria-label for each row selection. "
            "Bulk action toolbar announces selected count via aria-live. "
            "Slide-over panels trap focus, return focus on close. "
            "Status badges: never rely on color alone, always include text. "
            "Pagination: aria-label='Pagination', current page aria-current='page'."
        ),
    },
    "Blog": {
        "behavioral_description": (
            "Article list with card layout: image, title, excerpt, author, date. "
            "Category/tag filter without page reload. "
            "Article page: large header image, readable width (65ch max), "
            "table of contents sidebar for long articles. "
            "Code blocks with syntax highlighting and copy button. "
            "Related articles at bottom. Newsletter CTA inline or sticky."
        ),
        "accessibility_notes": (
            "Articles use proper heading hierarchy (h1 title, h2/h3 sections). "
            "Images have descriptive alt text. Code blocks use aria-label. "
            "Table of contents uses nav with aria-label='Table of contents'. "
            "Reading time estimate for screen readers. "
            "Link text is descriptive (not 'Read more' — use 'Read: Article Title')."
        ),
    },
    "Analytics": {
        "behavioral_description": (
            "Dashboard loads with date range defaulting to last 30 days. "
            "Charts update on date range change with loading skeleton. "
            "KPI cards show value, trend arrow, and percentage change. "
            "Hover on chart data points shows tooltip with exact values. "
            "Export data as CSV. Share dashboard via link. "
            "Comparison mode: overlay previous period as dashed line. "
            "Drill-down: click chart segment to filter table below."
        ),
        "accessibility_notes": (
            "Charts need aria-label summarizing the trend ('Revenue up 15% this month'). "
            "KPI trend indicators: use text alongside arrows ('+15%' not just green arrow). "
            "Data tables: sortable with aria-sort, filterable with live region updates. "
            "Date range picker: fully keyboard accessible with arrow key navigation. "
            "Export button: aria-label includes format ('Export as CSV')."
        ),
    },
    "SaaS": {
        "behavioral_description": (
            "Hero with headline, subheadline, email capture or CTA button. "
            "Social proof bar (logos or metrics). Feature sections with alternating layout. "
            "Testimonial carousel or grid. Pricing section with toggle. "
            "FAQ accordion. Footer with sitemap, social links, legal. "
            "Sticky CTA on scroll past hero."
        ),
        "accessibility_notes": (
            "Same as Landing Page. Additionally: "
            "Logo bar images need alt text (company names). "
            "Testimonials have proper cite elements. "
            "Sticky CTA doesn't obscure content and can be dismissed."
        ),
    },
    "Corporate": {
        "behavioral_description": (
            "Professional layout with clear information hierarchy. "
            "Hero with brand imagery and mission statement. "
            "Team section with headshots and roles. Partners/clients logo grid. "
            "Contact section with form and office locations. "
            "Careers link. Press/news section."
        ),
        "accessibility_notes": (
            "Team member images need name alt text. "
            "Map embed needs aria-label and keyboard fallback. "
            "Contact form follows accessible form patterns. "
            "Logo images need company name alt text."
        ),
    },
    "Documentation": {
        "behavioral_description": (
            "Left sidebar navigation with collapsible sections. "
            "Search with instant results (algolia-style). "
            "Code blocks with copy button, language selector, line highlighting. "
            "Breadcrumb navigation. Previous/Next page links at bottom. "
            "Table of contents in right sidebar for current page. "
            "Version selector in header."
        ),
        "accessibility_notes": (
            "Sidebar uses nav with aria-label='Documentation navigation'. "
            "Expandable sections use aria-expanded. "
            "Code blocks have aria-label with language. Copy button announces success. "
            "Search results use aria-live for dynamic updates. "
            "Breadcrumbs use nav with aria-label='Breadcrumb'."
        ),
    },
}

# ============================================================
# 2. SEMANTIC TOKEN SETS — Real, usable design tokens
# ============================================================
SEMANTIC_TOKENS = {
    "light": {
        "color-background": "hsl(0 0% 100%)",
        "color-background-secondary": "hsl(210 40% 96.1%)",
        "color-background-tertiary": "hsl(210 40% 98%)",
        "color-foreground": "hsl(222.2 84% 4.9%)",
        "color-foreground-secondary": "hsl(215.4 16.3% 46.9%)",
        "color-primary": "hsl(222.2 47.4% 11.2%)",
        "color-primary-foreground": "hsl(210 40% 98%)",
        "color-destructive": "hsl(0 84.2% 60.2%)",
        "color-border": "hsl(214.3 31.8% 91.4%)",
        "color-input": "hsl(214.3 31.8% 91.4%)",
        "color-ring": "hsl(222.2 84% 4.9%)",
        "color-accent": "hsl(210 40% 96.1%)",
        "color-accent-foreground": "hsl(222.2 47.4% 11.2%)",
        "color-muted": "hsl(210 40% 96.1%)",
        "color-muted-foreground": "hsl(215.4 16.3% 46.9%)",
        "color-card": "hsl(0 0% 100%)",
        "color-card-foreground": "hsl(222.2 84% 4.9%)",
        "color-popover": "hsl(0 0% 100%)",
        "color-popover-foreground": "hsl(222.2 84% 4.9%)",
        "spacing-0": "0px",
        "spacing-1": "4px",
        "spacing-2": "8px",
        "spacing-3": "12px",
        "spacing-4": "16px",
        "spacing-5": "20px",
        "spacing-6": "24px",
        "spacing-8": "32px",
        "spacing-10": "40px",
        "spacing-12": "48px",
        "spacing-16": "64px",
        "radius-sm": "calc(0.5rem - 2px)",
        "radius-md": "0.5rem",
        "radius-lg": "0.75rem",
        "radius-xl": "1rem",
        "radius-full": "9999px",
        "font-sans": "Inter, system-ui, -apple-system, sans-serif",
        "font-mono": "JetBrains Mono, Fira Code, monospace",
        "font-size-xs": "0.75rem",
        "font-size-sm": "0.875rem",
        "font-size-base": "1rem",
        "font-size-lg": "1.125rem",
        "font-size-xl": "1.25rem",
        "font-size-2xl": "1.5rem",
        "font-size-3xl": "1.875rem",
        "font-size-4xl": "2.25rem",
        "shadow-sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
        "shadow-md": "0 4px 6px -1px rgb(0 0 0 / 0.1)",
        "shadow-lg": "0 10px 15px -3px rgb(0 0 0 / 0.1)",
        "transition-fast": "150ms cubic-bezier(0.4, 0, 0.2, 1)",
        "transition-normal": "200ms cubic-bezier(0.4, 0, 0.2, 1)",
        "transition-slow": "300ms cubic-bezier(0.4, 0, 0.2, 1)",
    },
    "dark": {
        "color-background": "hsl(222.2 84% 4.9%)",
        "color-background-secondary": "hsl(217.2 32.6% 17.5%)",
        "color-background-tertiary": "hsl(222.2 47.4% 11.2%)",
        "color-foreground": "hsl(210 40% 98%)",
        "color-foreground-secondary": "hsl(215 20.2% 65.1%)",
        "color-primary": "hsl(210 40% 98%)",
        "color-primary-foreground": "hsl(222.2 47.4% 11.2%)",
        "color-destructive": "hsl(0 62.8% 30.6%)",
        "color-border": "hsl(217.2 32.6% 17.5%)",
        "color-input": "hsl(217.2 32.6% 17.5%)",
        "color-ring": "hsl(212.7 26.8% 83.9%)",
        "color-accent": "hsl(217.2 32.6% 17.5%)",
        "color-accent-foreground": "hsl(210 40% 98%)",
        "color-muted": "hsl(217.2 32.6% 17.5%)",
        "color-muted-foreground": "hsl(215 20.2% 65.1%)",
        "color-card": "hsl(222.2 84% 4.9%)",
        "color-card-foreground": "hsl(210 40% 98%)",
    },
}

# ============================================================
# 3. COMPONENT CODE TEMPLATES — Real, copy-paste-able code
# ============================================================
COMPONENT_CODE = {
    "Button": {
        "shadcn": '''import { Button } from "@/components/ui/button"

// Variants: default, destructive, outline, secondary, ghost, link
// Sizes: default, sm, lg, icon
<Button variant="default" size="default">Click me</Button>
<Button variant="destructive">Delete</Button>
<Button variant="outline" size="sm">Cancel</Button>
<Button disabled>Disabled</Button>
<Button asChild><a href="/link">Link Button</a></Button>''',
        "tailwind": '''<button className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50">
  Click me
</button>''',
    },
    "Card": {
        "shadcn": '''import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"

<Card>
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
    <CardDescription>Card description goes here.</CardDescription>
  </CardHeader>
  <CardContent>
    <p>Card content</p>
  </CardContent>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>''',
    },
    "Data Table": {
        "shadcn": '''import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Name</TableHead>
      <TableHead>Status</TableHead>
      <TableHead className="text-right">Amount</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {data.map((row) => (
      <TableRow key={row.id}>
        <TableCell className="font-medium">{row.name}</TableCell>
        <TableCell><Badge variant={row.status}>{row.status}</Badge></TableCell>
        <TableCell className="text-right">{row.amount}</TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>''',
    },
    "Form": {
        "shadcn": '''import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"

<form onSubmit={handleSubmit}>
  <div className="grid gap-4">
    <div className="grid gap-2">
      <Label htmlFor="email">Email</Label>
      <Input id="email" type="email" placeholder="you@example.com" required />
    </div>
    <div className="grid gap-2">
      <Label htmlFor="password">Password</Label>
      <Input id="password" type="password" required />
    </div>
    <Button type="submit" className="w-full">Sign In</Button>
  </div>
</form>''',
    },
    "Navigation Bar": {
        "shadcn": '''import { NavigationMenu, NavigationMenuList, NavigationMenuItem, NavigationMenuLink } from "@/components/ui/navigation-menu"

<header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
  <div className="container flex h-14 items-center">
    <NavigationMenu>
      <NavigationMenuList>
        <NavigationMenuItem>
          <NavigationMenuLink href="/">Home</NavigationMenuLink>
        </NavigationMenuItem>
      </NavigationMenuList>
    </NavigationMenu>
    <div className="ml-auto flex items-center gap-2">
      <Button variant="ghost" size="sm">Sign In</Button>
      <Button size="sm">Get Started</Button>
    </div>
  </div>
</header>''',
    },
    "Sidebar": {
        "shadcn": '''import { Sidebar, SidebarContent, SidebarGroup, SidebarGroupLabel, SidebarMenu, SidebarMenuItem, SidebarMenuButton } from "@/components/ui/sidebar"

<Sidebar>
  <SidebarContent>
    <SidebarGroup>
      <SidebarGroupLabel>Platform</SidebarGroupLabel>
      <SidebarMenu>
        <SidebarMenuItem>
          <SidebarMenuButton asChild>
            <a href="/dashboard"><LayoutDashboard className="mr-2 h-4 w-4" />Dashboard</a>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarGroup>
  </SidebarContent>
</Sidebar>''',
    },
    "Chart": {
        "shadcn": '''import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid } from "recharts"

const chartConfig = { revenue: { label: "Revenue", color: "hsl(var(--chart-1))" } }

<ChartContainer config={chartConfig} className="h-[300px]">
  <AreaChart data={data}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="month" />
    <YAxis />
    <ChartTooltip content={<ChartTooltipContent />} />
    <Area type="monotone" dataKey="revenue" fill="var(--color-revenue)" stroke="var(--color-revenue)" />
  </AreaChart>
</ChartContainer>''',
    },
    "Modal": {
        "shadcn": '''import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"

<Dialog>
  <DialogTrigger asChild><Button variant="outline">Open</Button></DialogTrigger>
  <DialogContent className="sm:max-w-[425px]">
    <DialogHeader>
      <DialogTitle>Edit Profile</DialogTitle>
      <DialogDescription>Make changes to your profile here.</DialogDescription>
    </DialogHeader>
    <div className="grid gap-4 py-4">
      {/* Form fields */}
    </div>
    <DialogFooter>
      <Button type="submit">Save changes</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>''',
    },
    "Dropdown": {
        "shadcn": '''import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

<Select>
  <SelectTrigger className="w-[180px]">
    <SelectValue placeholder="Select option" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="option1">Option 1</SelectItem>
    <SelectItem value="option2">Option 2</SelectItem>
    <SelectItem value="option3">Option 3</SelectItem>
  </SelectContent>
</Select>''',
    },
    "Tabs": {
        "shadcn": '''import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

<Tabs defaultValue="tab1" className="w-full">
  <TabsList>
    <TabsTrigger value="tab1">Overview</TabsTrigger>
    <TabsTrigger value="tab2">Analytics</TabsTrigger>
    <TabsTrigger value="tab3">Settings</TabsTrigger>
  </TabsList>
  <TabsContent value="tab1">Overview content</TabsContent>
  <TabsContent value="tab2">Analytics content</TabsContent>
  <TabsContent value="tab3">Settings content</TabsContent>
</Tabs>''',
    },
    "Search Bar": {
        "shadcn": '''import { Input } from "@/components/ui/input"
import { Search } from "lucide-react"

<div className="relative">
  <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
  <Input type="search" placeholder="Search..." className="pl-8" />
</div>''',
    },
    "Avatar": {
        "shadcn": '''import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

<Avatar>
  <AvatarImage src="/avatar.jpg" alt="User Name" />
  <AvatarFallback>UN</AvatarFallback>
</Avatar>''',
    },
    "Badge": {
        "shadcn": '''import { Badge } from "@/components/ui/badge"

<Badge variant="default">Active</Badge>
<Badge variant="secondary">Draft</Badge>
<Badge variant="destructive">Error</Badge>
<Badge variant="outline">Pending</Badge>''',
    },
    "Hero Section": {
        "tailwind": '''<section className="relative overflow-hidden bg-background py-24 sm:py-32">
  <div className="mx-auto max-w-7xl px-6 lg:px-8">
    <div className="mx-auto max-w-2xl text-center">
      <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-6xl">
        Your headline here
      </h1>
      <p className="mt-6 text-lg leading-8 text-muted-foreground">
        A compelling subheadline that explains your value proposition.
      </p>
      <div className="mt-10 flex items-center justify-center gap-x-6">
        <Button size="lg">Get Started</Button>
        <Button variant="ghost" size="lg">Learn more →</Button>
      </div>
    </div>
  </div>
</section>''',
    },
    "Pricing Table": {
        "shadcn": '''<div className="grid gap-8 md:grid-cols-3">
  {plans.map((plan) => (
    <Card key={plan.name} className={plan.popular ? "border-primary shadow-lg" : ""}>
      <CardHeader>
        {plan.popular && <Badge className="w-fit">Most Popular</Badge>}
        <CardTitle>{plan.name}</CardTitle>
        <div className="text-3xl font-bold">${plan.price}<span className="text-sm font-normal text-muted-foreground">/mo</span></div>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2">
          {plan.features.map((f) => (
            <li key={f} className="flex items-center gap-2">
              <Check className="h-4 w-4 text-primary" />{f}
            </li>
          ))}
        </ul>
      </CardContent>
      <CardFooter>
        <Button className="w-full" variant={plan.popular ? "default" : "outline"}>
          {plan.cta}
        </Button>
      </CardFooter>
    </Card>
  ))}
</div>''',
    },
    "Stats": {
        "shadcn": '''<div className="grid gap-4 md:grid-cols-4">
  {stats.map((stat) => (
    <Card key={stat.label}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{stat.label}</CardTitle>
        <stat.icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{stat.value}</div>
        <p className="text-xs text-muted-foreground">
          <span className={stat.trend > 0 ? "text-green-500" : "text-red-500"}>
            {stat.trend > 0 ? "+" : ""}{stat.trend}%
          </span> from last month
        </p>
      </CardContent>
    </Card>
  ))}
</div>''',
    },
    "Footer": {
        "tailwind": '''<footer className="border-t bg-background">
  <div className="mx-auto max-w-7xl px-6 py-12 lg:px-8">
    <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
      {footerLinks.map((section) => (
        <div key={section.title}>
          <h3 className="text-sm font-semibold text-foreground">{section.title}</h3>
          <ul className="mt-4 space-y-2">
            {section.links.map((link) => (
              <li key={link.label}>
                <a href={link.href} className="text-sm text-muted-foreground hover:text-foreground">{link.label}</a>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
    <div className="mt-12 border-t pt-8 text-center text-sm text-muted-foreground">
      &copy; 2026 Company. All rights reserved.
    </div>
  </div>
</footer>''',
    },
}

# ============================================================
# 4. PAGE TYPE LAYOUT TEMPLATES — actual layout code
# ============================================================
PAGE_LAYOUTS = {
    "Dashboard": '''<div className="flex h-screen">
  {/* Sidebar */}
  <aside className="hidden w-64 border-r bg-background md:block">
    <Sidebar />
  </aside>
  {/* Main */}
  <main className="flex-1 overflow-y-auto">
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur">
      <div className="flex h-14 items-center px-6">
        <h1 className="text-lg font-semibold">Dashboard</h1>
        <div className="ml-auto flex items-center gap-4">
          <SearchBar />
          <Avatar />
        </div>
      </div>
    </header>
    <div className="p-6 space-y-6">
      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard />
      </div>
      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card><Chart /></Card>
        <Card><Chart /></Card>
      </div>
      {/* Table */}
      <Card><DataTable /></Card>
    </div>
  </main>
</div>''',
    "Landing Page": '''<div className="min-h-screen bg-background">
  <NavBar />
  <main>
    {/* Hero */}
    <section className="py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-6 lg:px-8 text-center">
        <h1 className="text-4xl font-bold sm:text-6xl">Headline</h1>
        <p className="mt-6 text-lg text-muted-foreground max-w-2xl mx-auto">Subheadline</p>
        <div className="mt-10 flex justify-center gap-4">
          <Button size="lg">Get Started</Button>
          <Button variant="outline" size="lg">Learn More</Button>
        </div>
      </div>
    </section>
    {/* Social Proof */}
    <section className="border-y bg-muted/50 py-12">
      <LogoBar />
    </section>
    {/* Features */}
    <section className="py-24">
      <FeatureGrid columns={3} />
    </section>
    {/* Testimonials */}
    <section className="bg-muted/50 py-24">
      <TestimonialCarousel />
    </section>
    {/* CTA */}
    <section className="py-24 text-center">
      <CTASection />
    </section>
  </main>
  <Footer />
</div>''',
    "Auth": '''<div className="flex min-h-screen items-center justify-center bg-background">
  <Card className="w-full max-w-sm">
    <CardHeader className="text-center">
      <Logo />
      <CardTitle>Welcome back</CardTitle>
      <CardDescription>Sign in to your account</CardDescription>
    </CardHeader>
    <CardContent className="space-y-4">
      {/* Social Login */}
      <div className="grid grid-cols-2 gap-2">
        <Button variant="outline"><GoogleIcon /> Google</Button>
        <Button variant="outline"><GitHubIcon /> GitHub</Button>
      </div>
      <Separator text="or continue with" />
      {/* Email Form */}
      <LoginForm />
    </CardContent>
    <CardFooter className="text-center text-sm text-muted-foreground">
      Don't have an account? <a href="/signup" className="text-primary hover:underline">Sign up</a>
    </CardFooter>
  </Card>
</div>''',
}


def enrich_all_patterns():
    """Apply behavioral templates, tokens, and component code to all patterns."""
    with open(PATTERNS_PATH) as f:
        patterns = json.load(f)
    
    enriched_behavior = 0
    enriched_tokens = 0
    enriched_code = 0
    
    for i, pattern in enumerate(patterns):
        page_type = pattern.get("page_type", "")
        color_mode = pattern.get("color_mode", "light")
        
        # Apply behavioral template
        if not pattern.get("behavioral_description"):
            for key, template in BEHAVIORAL_TEMPLATES.items():
                if key.lower() in page_type.lower() or page_type.lower() in key.lower():
                    patterns[i]["behavioral_description"] = template["behavioral_description"]
                    if not pattern.get("accessibility_notes"):
                        patterns[i]["accessibility_notes"] = template["accessibility_notes"]
                    enriched_behavior += 1
                    break
        
        # Apply semantic tokens
        if not pattern.get("semantic_tokens"):
            mode = "dark" if color_mode == "dark" else "light"
            patterns[i]["semantic_tokens"] = SEMANTIC_TOKENS[mode]
            enriched_tokens += 1
        
        # Apply layout notes with actual code
        if not pattern.get("layout_notes") and page_type in PAGE_LAYOUTS:
            patterns[i]["layout_notes"] = PAGE_LAYOUTS[page_type]
            enriched_code += 1
        
        # Enrich component hints with actual code
        ui_elements = pattern.get("ui_elements", [])
        existing_hints = pattern.get("component_hints", [])
        
        if ui_elements and not any(h.get("code") for h in existing_hints):
            new_hints = []
            for element in ui_elements[:8]:
                if element in COMPONENT_CODE:
                    code_data = COMPONENT_CODE[element]
                    hint = {
                        "name": element.replace(" ", ""),
                        "code": code_data.get("shadcn") or code_data.get("tailwind", ""),
                        "library": "shadcn" if "shadcn" in code_data else "tailwind",
                    }
                    new_hints.append(hint)
            if new_hints:
                patterns[i]["component_hints"] = new_hints
                enriched_code += 1
    
    # Sort by quality
    patterns.sort(key=lambda p: p.get("quality_score", 0), reverse=True)
    
    with open(PATTERNS_PATH, "w") as f:
        json.dump(patterns, f, indent=2)
    
    print(f"Enriched behavioral: {enriched_behavior}")
    print(f"Enriched tokens: {enriched_tokens}")
    print(f"Enriched code: {enriched_code}")
    print(f"Total: {len(patterns)}")
    
    # Verify coverage
    has_behavior = sum(1 for p in patterns if p.get("behavioral_description"))
    has_tokens = sum(1 for p in patterns if p.get("semantic_tokens"))
    has_a11y = sum(1 for p in patterns if p.get("accessibility_notes"))
    has_code = sum(1 for p in patterns if any(h.get("code") for h in p.get("component_hints", [])))
    has_layout_code = sum(1 for p in patterns if p.get("layout_notes") and "className" in str(p.get("layout_notes", "")))
    
    print(f"\nCoverage after enrichment:")
    print(f"  behavioral_description: {has_behavior}/{len(patterns)}")
    print(f"  semantic_tokens: {has_tokens}/{len(patterns)}")
    print(f"  accessibility_notes: {has_a11y}/{len(patterns)}")
    print(f"  component code: {has_code}/{len(patterns)}")
    print(f"  layout code: {has_layout_code}/{len(patterns)}")


if __name__ == "__main__":
    enrich_all_patterns()
