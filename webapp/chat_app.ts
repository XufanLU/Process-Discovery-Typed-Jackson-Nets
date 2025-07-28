// TypeScript file for extended functionality (optional)
// This file can be used for additional TypeScript features if needed

interface ProcessModel {
  places: Place[];
  transitions: Transition[];
  arcs: Arc[];
  collaborations?: Collaboration[];
  agents?: Agent[];
}

interface Place {
  id: string;
  label: string;
  x: number;
  y: number;
  type?: string;
}

interface Transition {
  id: string;
  label: string;
  x: number;
  y: number;
  type: 'agent' | 'service' | 'partner' | 'default';
}

interface Arc {
  source: { id?: string; x: number; y: number };
  target: { id?: string; x: number; y: number };
}

interface Collaboration {
  id: string;
  type: string;
  participants: string[];
}

interface Agent {
  id: string;
  name: string;
  transitions: string[];
}

// Additional TypeScript functionality can be added here
export { ProcessModel, Place, Transition, Arc, Collaboration, Agent };
