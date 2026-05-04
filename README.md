# Simple Physics Engine for Gaming - SWGCG 352

## Project Overview
A modular physics engine for computer graphics and game development, implementing particle systems, mass-spring models, PBD, rigid body dynamics, and kinematics.

## Phase 1 Deliverables (Week 8) ✓
- ✓ Project proposal
- ✓ Engine architecture design
- ✓ Particle simulation demo

## Phase 2 Deliverables (Week 9) ✓
- ✓ Particle effects demonstration
- ✓ Mass-spring system with structural springs
- ✓ Damping implementation
- ✓ Soft-body rope prototype

## Phase 3 Deliverables (Week 10) ✓
- ✓ Position-Based Dynamics implementation
- ✓ Distance constraints
- ✓ Constraint solver with iterations
- ✓ PBD rope and cloth simulation

## Architecture
```
src/
├── core/           # Core engine components
├── particles/      # Particle system module
├── springs/        # Mass-spring system
├── pbd/           # Position-Based Dynamics
├── rigidbody/     # Rigid body dynamics
├── kinematics/    # FK and IK
└── demo/          # Demo applications
```

## Getting Started

### Console Demos (Node.js)
```bash
# Run particle demo
npm run demo:particles

# Run mass-spring demo
npm run demo:springs

# Run PBD demo
npm run demo:pbd
```

### Visual Demo (Browser)
Open `src/demo/visualDemo.html` in your browser for an interactive demonstration of all physics modules.

## Technologies
- JavaScript/Canvas for rendering
- Modular ES6 architecture
