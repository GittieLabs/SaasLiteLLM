# LiteLLM Admin Panel

A modern, fully-featured admin panel for managing the SaaS LiteLLM API built with Next.js 15, React 19, TypeScript, and Tailwind CSS v4.

## Features

- **Dashboard**: Overview with statistics for organizations, teams, model groups, and credits
- **Organizations Management**: View and create organizations
- **Teams Management**: Manage teams with credits tracking and virtual keys
- **Model Groups**: Configure model routing groups with priority
- **Authentication**: Simple login system with role-based access (owner/user)
- **Clean UI**: Modern interface using Shadcn-inspired components
- **Full TypeScript**: Type-safe throughout the application

## Tech Stack

- **Next.js 15.5.5** - React framework with App Router
- **React 19.2.0** - UI library
- **TypeScript 5.9.3** - Type safety
- **Tailwind CSS 4.1.14** - Utility-first CSS framework
- **Radix UI** - Headless UI components
- **Lucide React** - Icon library

## Project Structure

```
admin-panel/
├── app/                          # Next.js App Router pages
│   ├── globals.css              # Global styles with Tailwind
│   ├── layout.tsx               # Root layout
│   ├── page.tsx                 # Dashboard page
│   ├── login/page.tsx           # Login page
│   ├── organizations/page.tsx   # Organizations management
│   ├── teams/page.tsx           # Teams management
│   └── model-groups/page.tsx    # Model groups management
├── components/                   # React components
│   ├── ui/                      # UI components (button, card, input, etc.)
│   ├── Sidebar.tsx              # Navigation sidebar
│   └── ProtectedRoute.tsx       # Authentication wrapper
├── lib/                         # Utility libraries
│   ├── auth.ts                  # Authentication logic
│   ├── api-client.ts            # API client for backend
│   └── utils.ts                 # Utility functions (cn helper)
├── types/                       # TypeScript type definitions
│   └── index.ts                 # Shared interfaces
├── .env.local                   # Environment variables
├── next.config.js               # Next.js configuration
├── tailwind.config.ts           # Tailwind CSS configuration
├── postcss.config.js            # PostCSS configuration
└── tsconfig.json                # TypeScript configuration
```

## Getting Started

### Prerequisites

- Node.js 18+ installed
- npm or yarn package manager
- SaaS LiteLLM API running on http://localhost:8003

### Installation

Dependencies are already installed. If you need to reinstall:

```bash
npm install
```

### Environment Variables

The `.env.local` file is already configured:

```env
NEXT_PUBLIC_API_URL=http://localhost:8003
```

### Running Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Building for Production

```bash
npm run build
npm start
```

## Authentication

The admin panel uses a simple localStorage-based authentication system for demo purposes.

**Demo Credentials:**

- **Admin User**:
  - Username: `admin`
  - Password: `admin123`
  - Role: `owner`

- **Regular User**:
  - Username: `user`
  - Password: `user123`
  - Role: `user`

## Pages Overview

### Dashboard (`/`)
- Overview statistics cards
- Recent activity feed
- Quick access to all sections

### Login (`/login`)
- Simple login form
- Credentials validation
- Redirect to dashboard on success

### Organizations (`/organizations`)
- List all organizations in a table
- Create new organizations
- View organization details (ID, name, status, created date)

### Teams (`/teams`)
- List all teams with credit information
- Create new teams
- View virtual keys and credits (allocated, used, remaining)
- Associate teams with organizations

### Model Groups (`/model-groups`)
- List all model routing groups
- Create new model groups
- View models in each group with priority
- Configure group settings

## API Integration

The admin panel connects to the SaaS LiteLLM API endpoints:

### Organizations
- `GET /api/organizations` - List organizations
- `GET /api/organizations/{id}` - Get organization
- `POST /api/organizations/create` - Create organization

### Teams
- `GET /api/teams/{id}` - Get team
- `POST /api/teams/create` - Create team

### Model Groups
- `GET /api/model-groups` - List model groups
- `POST /api/model-groups/create` - Create model group

### Credits
- `GET /api/credits/teams/{team_id}/balance` - Get team credits

## Components

### UI Components (`components/ui/`)
All components are built with Tailwind CSS and follow the Shadcn design system:

- **Button**: Multiple variants (default, destructive, outline, secondary, ghost, link)
- **Card**: Container with header, content, and footer sections
- **Input**: Form input with proper styling
- **Label**: Form label component
- **Table**: Data table with header, body, rows, and cells

### Layout Components

- **Sidebar**: Navigation menu with active state and logout
- **ProtectedRoute**: HOC for authenticating routes

## Styling

The project uses Tailwind CSS v4 with a custom theme:

- Custom color palette using CSS variables
- Responsive design
- Dark mode ready (theme not implemented yet)
- Consistent spacing and typography

## Type Safety

All components and functions are fully typed with TypeScript:

- `User` - User authentication
- `Organization` - Organization entity
- `Team` - Team with credits
- `ModelGroup` - Model routing configuration
- `AuditLog` - Activity logging

## Development Notes

### Mock Data
Currently, the admin panel uses mock data for demonstration. To connect to the real API:

1. Update the API client calls in each page
2. Remove mock data generation
3. Handle loading states and errors
4. Add proper API authentication headers

### Future Enhancements
- Real-time updates with WebSockets
- Advanced filtering and sorting
- Bulk operations
- Export functionality
- Dark mode toggle
- User profile management
- Audit log viewer
- API key management
- Team member management
- Advanced analytics

## Troubleshooting

### Build Errors
If you encounter build errors:
1. Clear Next.js cache: `rm -rf .next`
2. Reinstall dependencies: `rm -rf node_modules && npm install`
3. Check TypeScript errors: `npm run lint`

### API Connection Issues
- Ensure the backend API is running on http://localhost:8003
- Check CORS settings on the backend
- Verify API endpoints match the expected format

## License

ISC
