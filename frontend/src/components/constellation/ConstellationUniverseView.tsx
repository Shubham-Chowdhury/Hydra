import React, { useEffect, useRef, useState } from 'react';
import type {
  ProgrammeEvaluationDto,
  ProgrammeResponse,
  StudentProfileRequest,
} from '../../api/types';
import { FloatingCommandConsole } from './FloatingCommandConsole';
import { FloatingAnalysisCard } from './FloatingAnalysisCard';
import { RightInspectorPanel } from './RightInspectorPanel';
import { ArrowLeft, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

interface ConstellationUniverseViewProps {
  evaluations: ProgrammeEvaluationDto[];
  catalogProgrammes: ProgrammeResponse[];
  profile?: StudentProfileRequest;
  onSelectPreset: (preset: 'eligible' | 'ineligible' | 'needs_review' | 'unaffordable') => void;
  onExploreDetails: (programmeId: string) => void;
}

interface ConstellationNode {
  id: string;
  label: string;
  x: number;
  y: number;
  radius: number;
  color: string;
  haloColor: string;
  type: 'core' | 'cluster' | 'programme' | 'satellite';
  percentage?: number;
  countBadge?: number;
  evaluation?: ProgrammeEvaluationDto;
  satellites?: Array<{ label: string; count: number; angle: number; dist: number }>;
}

export const ConstellationUniverseView: React.FC<ConstellationUniverseViewProps> = ({
  evaluations,
  catalogProgrammes,
  profile,
  onSelectPreset,
  onExploreDetails,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // View state
  const [isAnalysisOpen, setIsAnalysisOpen] = useState(false);
  const [selectedNode, setSelectedNode] = useState<ConstellationNode | null>(null);
  const [selectedEvaluation, setSelectedEvaluation] = useState<ProgrammeEvaluationDto | null>(null);
  const [activeYear, setActiveYear] = useState<number>(2025);
  const [searchFilter, setSearchFilter] = useState<string>('');

  // Camera transform
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [zoom, setZoom] = useState<number>(1);
  const isDraggingRef = useRef<boolean>(false);
  const dragStartRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  // Photon beam animation time
  const animTimeRef = useRef<number>(0);

  // Define Celestial Constellation Nodes
  const clusters: ConstellationNode[] = [
    {
      id: 'cluster_cs',
      label: 'Computer Science',
      x: 320,
      y: -80,
      radius: 28,
      color: '#D9659A',
      haloColor: 'rgba(217, 101, 154, 0.45)',
      type: 'cluster',
      percentage: 47,
      countBadge: 18,
      evaluation: evaluations.find((e) => e.programme_id === 'PROG_001') || evaluations[0],
      satellites: [
        { label: 'Software Eng', count: 12, angle: -0.4, dist: 80 },
        { label: 'Data Structs', count: 8, angle: 0.3, dist: 95 },
      ],
    },
    {
      id: 'cluster_ai',
      label: 'Robotics & AI',
      x: 360,
      y: 160,
      radius: 26,
      color: '#8F76DE',
      haloColor: 'rgba(143, 118, 222, 0.45)',
      type: 'cluster',
      percentage: 25,
      countBadge: 24,
      evaluation: evaluations.find((e) => e.programme_id === 'PROG_002') || evaluations[1],
      satellites: [
        { label: 'Sensors', count: 11, angle: 0.5, dist: 75 },
        { label: 'Firmware', count: 7, angle: -0.2, dist: 90 },
      ],
    },
    {
      id: 'cluster_ds',
      label: 'Data Science & Math',
      x: 180,
      y: 280,
      radius: 25,
      color: '#D9659A',
      haloColor: 'rgba(217, 101, 154, 0.4)',
      type: 'cluster',
      percentage: 33,
      countBadge: 13,
      evaluation: evaluations.find((e) => e.programme_id === 'PROG_003') || evaluations[2],
      satellites: [
        { label: 'Statistics', count: 20, angle: 0.8, dist: 70 },
        { label: 'Calculus', count: 16, angle: 1.4, dist: 85 },
      ],
    },
    {
      id: 'cluster_bio',
      label: 'Biotechnology',
      x: 420,
      y: 320,
      radius: 24,
      color: '#D9659A',
      haloColor: 'rgba(217, 101, 154, 0.4)',
      type: 'cluster',
      percentage: 11,
      countBadge: 8,
      evaluation: evaluations.find((e) => e.programme_id === 'PROG_004') || evaluations[3],
      satellites: [
        { label: 'Genomics', count: 5, angle: 0.2, dist: 80 },
        { label: 'Bioinformatics', count: 14, angle: 0.9, dist: 90 },
      ],
    },
    {
      id: 'cluster_reg',
      label: 'Justice & Compliance',
      x: -60,
      y: 320,
      radius: 25,
      color: '#8F76DE',
      haloColor: 'rgba(143, 118, 222, 0.4)',
      type: 'cluster',
      percentage: 13,
      countBadge: 36,
      satellites: [
        { label: 'AICTE Criteria', count: 9, angle: 1.8, dist: 75 },
        { label: 'CBSE 10+2', count: 13, angle: 2.4, dist: 95 },
      ],
    },
    {
      id: 'cluster_culture',
      label: 'Culture & Humanities',
      x: -300,
      y: 180,
      radius: 25,
      color: '#D9659A',
      haloColor: 'rgba(217, 101, 154, 0.4)',
      type: 'cluster',
      percentage: 22,
      countBadge: 16,
      satellites: [{ label: 'Design Theory', count: 21, angle: 2.8, dist: 80 }],
    },
    {
      id: 'cluster_energy',
      label: 'Energy & Electrical',
      x: -240,
      y: -180,
      radius: 26,
      color: '#D9659A',
      haloColor: 'rgba(217, 101, 154, 0.45)',
      type: 'cluster',
      percentage: 38,
      countBadge: 19,
      satellites: [
        { label: 'Power Grid', count: 10, angle: -2.2, dist: 85 },
        { label: 'Solar Tech', count: 17, angle: -1.7, dist: 70 },
      ],
    },
    {
      id: 'cluster_sec',
      label: 'Security & Safety',
      x: 480,
      y: -180,
      radius: 26,
      color: '#E5B869',
      haloColor: 'rgba(229, 184, 105, 0.45)',
      type: 'cluster',
      percentage: 23,
      countBadge: 12,
      satellites: [{ label: 'Cyber Systems', count: 5, angle: -0.6, dist: 80 }],
    },
  ];

  // Canvas render animation loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;

    const handleResize = () => {
      canvas.width = canvas.parentElement?.clientWidth || window.innerWidth;
      canvas.height = canvas.parentElement?.clientHeight || window.innerHeight;
    };
    handleResize();
    window.addEventListener('resize', handleResize);

    const render = () => {
      animTimeRef.current += 0.015;
      const t = animTimeRef.current;

      const w = canvas.width;
      const h = canvas.height;

      // 1. Draw Deep Cosmic Background with Subtle Ambient Glows
      ctx.fillStyle = '#070B0E';
      ctx.fillRect(0, 0, w, h);

      // Radial ambient lighting
      const gradBg = ctx.createRadialGradient(w / 2, h / 2, 50, w / 2, h / 2, Math.max(w, h));
      gradBg.addColorStop(0, 'rgba(12, 28, 33, 0.6)');
      gradBg.addColorStop(0.5, 'rgba(7, 18, 22, 0.85)');
      gradBg.addColorStop(1, '#070B0E');
      ctx.fillStyle = gradBg;
      ctx.fillRect(0, 0, w, h);

      ctx.save();
      // Apply Camera Transform
      const originX = w / 2 + pan.x;
      const originY = h / 2 + pan.y;
      ctx.translate(originX, originY);
      ctx.scale(zoom, zoom);

      // IF FOCUSED NODE IS ACTIVE: Draw Focused Tree View (Matching frame_10.png & frame_15.png)
      if (selectedNode) {
        drawFocusedNodeView(ctx, selectedNode, t);
      } else {
        // FULL CONSTELLATION GALAXY VIEW (Matching frame_01.png, frame_18.png, frame_21.png)
        drawConstellationGalaxy(ctx, clusters, t);
      }

      ctx.restore();

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [pan, zoom, selectedNode, evaluations, searchFilter]);

  // Helper: Draw Full Galaxy Constellation
  const drawConstellationGalaxy = (
    ctx: CanvasRenderingContext2D,
    nodes: ConstellationNode[],
    t: number
  ) => {
    const center = { x: 0, y: 0 };

    // A. Draw Dual-Line Glowing Laser Beams from Center to Clusters
    nodes.forEach((node) => {
      const dx = node.x - center.x;
      const dy = node.y - center.y;

      // Glow beam background
      ctx.beginPath();
      ctx.moveTo(center.x, center.y);
      ctx.lineTo(node.x, node.y);
      ctx.strokeStyle = 'rgba(229, 184, 105, 0.12)';
      ctx.lineWidth = 14;
      ctx.stroke();

      // Sharp dual core rays
      ctx.beginPath();
      ctx.moveTo(center.x, center.y);
      ctx.lineTo(node.x, node.y);
      ctx.strokeStyle = 'rgba(229, 184, 105, 0.4)';
      ctx.lineWidth = 2.5;
      ctx.stroke();

      // Moving photon particles along the beam
      const particleProgress = (t * 0.4 + (node.percentage || 10) * 0.1) % 1;
      const px = center.x + dx * particleProgress;
      const py = center.y + dy * particleProgress;

      ctx.beginPath();
      ctx.arc(px, py, 3.5, 0, Math.PI * 2);
      ctx.fillStyle = '#FFFFFF';
      ctx.shadowColor = '#3DD9C4';
      ctx.shadowBlur = 10;
      ctx.fill();
      ctx.shadowBlur = 0;

      // Draw dotted connection to satellites
      if (node.satellites) {
        node.satellites.forEach((sat) => {
          const sx = node.x + Math.cos(sat.angle) * sat.dist;
          const sy = node.y + Math.sin(sat.angle) * sat.dist;

          ctx.beginPath();
          ctx.setLineDash([3, 4]);
          ctx.moveTo(node.x, node.y);
          ctx.lineTo(sx, sy);
          ctx.strokeStyle = 'rgba(141, 161, 168, 0.35)';
          ctx.lineWidth = 1;
          ctx.stroke();
          ctx.setLineDash([]);

          // Satellite dot
          ctx.beginPath();
          ctx.arc(sx, sy, 5, 0, Math.PI * 2);
          ctx.fillStyle = '#E5B869';
          ctx.shadowColor = 'rgba(229, 184, 105, 0.8)';
          ctx.shadowBlur = 8;
          ctx.fill();
          ctx.shadowBlur = 0;

          // Satellite number pill
          ctx.fillStyle = '#0C1417';
          ctx.fillRect(sx + 8, sy - 9, 18, 14);
          ctx.strokeStyle = '#233F4A';
          ctx.lineWidth = 1;
          ctx.strokeRect(sx + 8, sy - 9, 18, 14);

          ctx.fillStyle = '#F0F4F5';
          ctx.font = 'bold 9px monospace';
          ctx.fillText(String(sat.count), sx + 12, sy + 2);
        });
      }
    });

    // B. Draw Inter-Cluster Constellation Lines
    for (let i = 0; i < nodes.length; i++) {
      const next = nodes[(i + 1) % nodes.length];
      ctx.beginPath();
      ctx.setLineDash([2, 5]);
      ctx.moveTo(nodes[i].x, nodes[i].y);
      ctx.lineTo(next.x, next.y);
      ctx.strokeStyle = 'rgba(61, 217, 196, 0.2)';
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // C. Draw Planetary Cluster Nodes
    nodes.forEach((node) => {
      const isSearchMatch =
        searchFilter.trim() !== '' &&
        node.label.toLowerCase().includes(searchFilter.toLowerCase());

      // Layered outer aura rings
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius + (isSearchMatch ? 18 : 12), 0, Math.PI * 2);
      ctx.strokeStyle = isSearchMatch ? '#3DD9C4' : node.haloColor;
      ctx.lineWidth = isSearchMatch ? 2.5 : 1.5;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius + 6, 0, Math.PI * 2);
      ctx.strokeStyle = isSearchMatch ? '#3DD9C4' : node.haloColor;
      ctx.lineWidth = 1;
      ctx.stroke();

      // Spherical Glossy Marble Node
      const gradNode = ctx.createRadialGradient(
        node.x - node.radius * 0.3,
        node.y - node.radius * 0.3,
        2,
        node.x,
        node.y,
        node.radius
      );
      gradNode.addColorStop(0, '#FFFFFF');
      gradNode.addColorStop(0.3, node.color);
      gradNode.addColorStop(1, '#0C1417');
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
      ctx.fillStyle = gradNode;
      ctx.shadowColor = node.color;
      ctx.shadowBlur = 18;
      ctx.fill();
      ctx.shadowBlur = 0;

      // Label Text & Percentage Pill
      ctx.fillStyle = '#FFFFFF';
      ctx.font = 'bold 12px sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText(node.label, node.x + node.radius + 8, node.y - 2);

      if (node.percentage !== undefined) {
        ctx.fillStyle = 'rgba(22, 39, 46, 0.85)';
        ctx.fillRect(node.x + node.radius + 8, node.y + 6, 32, 16);
        ctx.strokeStyle = '#233F4A';
        ctx.lineWidth = 1;
        ctx.strokeRect(node.x + node.radius + 8, node.y + 6, 32, 16);

        ctx.fillStyle = '#3DD9C4';
        ctx.font = 'bold 10px monospace';
        ctx.fillText(`${node.percentage}%`, node.x + node.radius + 12, node.y + 18);
      }
    });

    // D. Draw Central Master Celestial Orb ("Hydra Core / Digital Twin")
    const coreR = 48;
    // Layered Concentric Rings with Radial Hatched Dashes
    for (let r = coreR + 8; r <= coreR + 32; r += 8) {
      ctx.beginPath();
      ctx.arc(center.x, center.y, r, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(229, 184, 105, 0.25)';
      ctx.setLineDash([2, 4]);
      ctx.lineWidth = 1.2;
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Outer corona glow
    const coreGlow = ctx.createRadialGradient(center.x, center.y, 10, center.x, center.y, coreR * 1.8);
    coreGlow.addColorStop(0, 'rgba(255, 230, 160, 0.9)');
    coreGlow.addColorStop(0.4, 'rgba(229, 184, 105, 0.45)');
    coreGlow.addColorStop(1, 'rgba(229, 184, 105, 0)');
    ctx.fillStyle = coreGlow;
    ctx.beginPath();
    ctx.arc(center.x, center.y, coreR * 1.8, 0, Math.PI * 2);
    ctx.fill();

    // Central Sphere
    const coreSphere = ctx.createRadialGradient(
      center.x - coreR * 0.35,
      center.y - coreR * 0.35,
      4,
      center.x,
      center.y,
      coreR
    );
    coreSphere.addColorStop(0, '#FFFFFF');
    coreSphere.addColorStop(0.2, '#FFE8B3');
    coreSphere.addColorStop(0.7, '#D49F43');
    coreSphere.addColorStop(1, '#61430F');
    ctx.beginPath();
    ctx.arc(center.x, center.y, coreR, 0, Math.PI * 2);
    ctx.fillStyle = coreSphere;
    ctx.shadowColor = '#E5B869';
    ctx.shadowBlur = 30;
    ctx.fill();
    ctx.shadowBlur = 0;

    // Center Core Label
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 15px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Hydra Twin Core', center.x + coreR + 12, center.y - 2);

    ctx.fillStyle = 'rgba(22, 39, 46, 0.9)';
    ctx.fillRect(center.x + coreR + 12, center.y + 6, 42, 18);
    ctx.strokeStyle = '#E5B869';
    ctx.lineWidth = 1;
    ctx.strokeRect(center.x + coreR + 12, center.y + 6, 42, 18);

    ctx.fillStyle = '#E5B869';
    ctx.font = 'bold 11px monospace';
    ctx.fillText('91%', center.x + coreR + 18, center.y + 19);
  };

  // Helper: Draw Focused Node View (Matching frame_10.png & frame_15.png)
  const drawFocusedNodeView = (
    ctx: CanvasRenderingContext2D,
    node: ConstellationNode,
    t: number
  ) => {
    const focusX = -180;
    const focusY = 0;
    const r = 36;

    // Pulsing Serrated Corona around Focused Node
    ctx.beginPath();
    const spikes = 36;
    for (let i = 0; i < spikes; i++) {
      const angle = (i / spikes) * Math.PI * 2 + t * 0.5;
      const spikeR = r + 16 + Math.sin(angle * 6 + t * 4) * 5;
      const px = focusX + Math.cos(angle) * spikeR;
      const py = focusY + Math.sin(angle) * spikeR;
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.closePath();
    ctx.strokeStyle = 'rgba(143, 118, 222, 0.6)';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Marble sphere
    const marbleGrad = ctx.createRadialGradient(focusX - r * 0.3, focusY - r * 0.3, 3, focusX, focusY, r);
    marbleGrad.addColorStop(0, '#FFFFFF');
    marbleGrad.addColorStop(0.3, '#8F76DE');
    marbleGrad.addColorStop(1, '#1A142E');
    ctx.beginPath();
    ctx.arc(focusX, focusY, r, 0, Math.PI * 2);
    ctx.fillStyle = marbleGrad;
    ctx.shadowColor = '#8F76DE';
    ctx.shadowBlur = 25;
    ctx.fill();
    ctx.shadowBlur = 0;

    // Focused Node Title on Left
    ctx.fillStyle = '#F0F4F5';
    ctx.font = 'bold 16px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(node.evaluation?.programme_title || node.label, focusX, focusY - r - 20);

    ctx.fillStyle = '#8DA1A8';
    ctx.font = '12px monospace';
    ctx.fillText(`ID: ${node.evaluation?.programme_id || node.id}`, focusX, focusY - r - 4);

    // GAPS Badge below node
    ctx.fillStyle = '#142227';
    ctx.fillRect(focusX - 35, focusY + r + 15, 70, 20);
    ctx.strokeStyle = '#233F4A';
    ctx.lineWidth = 1;
    ctx.strokeRect(focusX - 35, focusY + r + 15, 70, 20);

    ctx.fillStyle = '#8DA1A8';
    ctx.font = 'bold 10px monospace';
    ctx.fillText('GAPS 12', focusX, focusY + r + 29);

    // 5 Category Cards Radiating from Entity (Matching frame_10.png)
    const categoryCards = [
      { id: 'cat_req', label: 'Prerequisites', count: 18, y: -130 },
      { id: 'cat_auth', label: 'Authorities', count: 3, y: -65 },
      { id: 'cat_rules', label: 'Evaluated Rules', count: 24, y: 0, active: true },
      { id: 'cat_kpi', label: 'KPIs & Ranks', count: 32, y: 65 },
      { id: 'cat_finance', label: 'Financial / Quotas', count: 12, y: 130 },
    ];

    const cardStartX = focusX + r + 70;

    categoryCards.forEach((cat) => {
      const cardY = focusY + cat.y;

      // Curved Bezier Connector from Node to Card
      ctx.beginPath();
      ctx.moveTo(focusX + r, focusY);
      ctx.bezierCurveTo(focusX + r + 40, focusY, cardStartX - 40, cardY, cardStartX, cardY);
      ctx.strokeStyle = cat.active ? '#E5B869' : 'rgba(141, 161, 168, 0.3)';
      ctx.lineWidth = cat.active ? 2 : 1;
      ctx.stroke();

      // Card Container Pill
      const cardW = 140;
      const cardH = 46;
      ctx.fillStyle = cat.active ? '#1A2930' : '#111A1E';
      ctx.fillRect(cardStartX, cardY - cardH / 2, cardW, cardH);
      ctx.strokeStyle = cat.active ? '#E5B869' : '#1E343D';
      ctx.lineWidth = cat.active ? 2 : 1;
      ctx.strokeRect(cardStartX, cardY - cardH / 2, cardW, cardH);

      // Icon & Number
      ctx.fillStyle = cat.active ? '#E5B869' : '#F0F4F5';
      ctx.font = 'bold 14px monospace';
      ctx.textAlign = 'left';
      ctx.fillText(String(cat.count), cardStartX + 12, cardY - 2);

      // Label
      ctx.fillStyle = '#8DA1A8';
      ctx.font = '10px sans-serif';
      ctx.fillText(cat.label, cardStartX + 12, cardY + 14);

      // IF ACTIVE CARD: Fanned curved beam array shooting to the right!
      if (cat.active) {
        const fanCount = 14;
        const fanStartX = cardStartX + cardW;
        for (let j = 0; j < fanCount; j++) {
          const spreadY = focusY - 140 + j * 24;
          const targetX = fanStartX + 130 + Math.sin(j * 0.4) * 20;

          ctx.beginPath();
          ctx.moveTo(fanStartX, cardY);
          ctx.bezierCurveTo(fanStartX + 60, cardY, targetX - 50, spreadY, targetX, spreadY);
          ctx.strokeStyle = `rgba(229, 184, 105, ${0.15 + (j % 3) * 0.2})`;
          ctx.lineWidth = 1.2;
          ctx.stroke();

          // Particle endpoints
          ctx.beginPath();
          ctx.arc(targetX, spreadY, 3, 0, Math.PI * 2);
          ctx.fillStyle = j % 2 === 0 ? '#3DD9C4' : '#E5B869';
          ctx.fill();

          // Small tag on endpoint
          ctx.fillStyle = '#8DA1A8';
          ctx.font = '9px monospace';
          ctx.fillText(`Rule #${100 + j}`, targetX + 8, spreadY + 3);
        }
      }
    });
  };

  // Canvas Mouse Click / Interaction Detection
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    const originX = canvas.width / 2 + pan.x;
    const originY = canvas.height / 2 + pan.y;

    const worldX = (clickX - originX) / zoom;
    const worldY = (clickY - originY) / zoom;

    // Check hit test against clusters
    let hitNode: ConstellationNode | null = null;
    for (const node of clusters) {
      const dx = worldX - node.x;
      const dy = worldY - node.y;
      if (Math.sqrt(dx * dx + dy * dy) <= node.radius + 15) {
        hitNode = node;
        break;
      }
    }

    if (hitNode) {
      setSelectedNode(hitNode);
      const evalDto = hitNode.evaluation || evaluations[0] || null;
      setSelectedEvaluation(evalDto);
    } else {
      // Clicked on empty space: if in focused mode, return to galaxy
      if (selectedNode) {
        setSelectedNode(null);
        setSelectedEvaluation(null);
      }
    }
  };

  // Dragging / Panning handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    isDraggingRef.current = true;
    dragStartRef.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDraggingRef.current) return;
    setPan({
      x: e.clientX - dragStartRef.current.x,
      y: e.clientY - dragStartRef.current.y,
    });
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const handleWheel = (e: React.WheelEvent) => {
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom((prev) => Math.min(Math.max(prev * delta, 0.5), 2.5));
  };

  const handleSelectProgrammeFromAnalysis = (progId: string) => {
    const matched = evaluations.find((e) => e.programme_id === progId) || evaluations[0];
    const matchedCluster = clusters.find((c) => c.evaluation?.programme_id === progId) || clusters[0];
    setSelectedNode(matchedCluster);
    setSelectedEvaluation(matched);
    setIsAnalysisOpen(false);
  };

  const years = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026];

  return (
    <div
      className="relative w-full h-[calc(100vh-4rem)] overflow-hidden bg-[#070B0E] select-none"
      onWheel={handleWheel}
    >
      {/* Interactive Canvas */}
      <canvas
        ref={canvasRef}
        onClick={handleCanvasClick}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        className="w-full h-full cursor-grab active:cursor-grabbing block"
      />

      {/* Back to Galaxy Button (if focused node is active) */}
      {selectedNode && (
        <button
          onClick={() => {
            setSelectedNode(null);
            setSelectedEvaluation(null);
          }}
          className="absolute top-6 left-6 z-30 flex items-center gap-2 px-4 py-2 rounded-2xl bg-[#0C1518]/90 backdrop-blur-xl border border-[#1E343D] text-xs font-bold text-[#3DD9C4] hover:bg-[#152329] shadow-xl transition-all"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Galaxy View</span>
        </button>
      )}

      {/* Left Vertical Timeline Slider (Matching frame_21.png) */}
      <div className="absolute left-6 top-1/2 -translate-y-1/2 z-30 flex flex-col items-center gap-3">
        <div className="w-0.5 h-16 bg-gradient-to-b from-transparent to-[#1E343D]" />
        {years.slice(2).map((year) => {
          const isActive = year === activeYear;
          return (
            <button
              key={year}
              onClick={() => setActiveYear(year)}
              className={`relative px-3 py-1.5 rounded-full font-mono text-xs font-bold transition-all ${
                isActive
                  ? 'bg-[#142227] text-[#3DD9C4] border border-[#3DD9C4] glow-cyan shadow-lg scale-110'
                  : 'text-[#576A70] hover:text-[#8DA1A8]'
              }`}
            >
              {year}
            </button>
          );
        })}
        <div className="w-0.5 h-16 bg-gradient-to-t from-transparent to-[#1E343D]" />
      </div>

      {/* Bottom-Left Floating Legend (Matching frame_21.png) */}
      <div className="absolute left-6 bottom-6 z-30 hidden sm:block p-3.5 rounded-2xl bg-[#0C1518]/85 backdrop-blur-xl border border-[#1E343D] text-[11px] space-y-2 shadow-xl">
        <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#576A70]">
          LEGEND
        </div>
        <div className="space-y-1.5 text-[#8DA1A8]">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-[#E5B869] shadow-xs" />
            <span>Digital Twin Master Core</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-[#D9659A]" />
            <span>Academic Clusters</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-[#8F76DE]" />
            <span>Evaluated Programmes</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-[#3DD9C4]" />
            <span>Deterministic Rules</span>
          </div>
          <div className="flex items-center justify-between pt-1 border-t border-[#1E343D] text-[10px] font-mono">
            <span>Cutoff GAPS: 32%</span>
            <span>Rules: 56%</span>
          </div>
        </div>
      </div>

      {/* Zoom / Reset Camera Controls on Top Right */}
      <div className="absolute top-6 right-6 z-30 flex items-center gap-1.5 p-1.5 rounded-2xl bg-[#0C1518]/85 backdrop-blur-xl border border-[#1E343D]">
        <button
          onClick={() => setZoom((prev) => Math.min(prev * 1.2, 2.5))}
          className="p-2 rounded-xl text-[#8DA1A8] hover:text-white hover:bg-[#16272E] transition-colors"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          onClick={() => setZoom((prev) => Math.max(prev * 0.8, 0.5))}
          className="p-2 rounded-xl text-[#8DA1A8] hover:text-white hover:bg-[#16272E] transition-colors"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          onClick={() => {
            setPan({ x: 0, y: 0 });
            setZoom(1);
          }}
          className="p-2 rounded-xl text-[#8DA1A8] hover:text-white hover:bg-[#16272E] transition-colors"
          title="Reset View"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      {/* Floating Pathway Analysis Card Popover (Matching frame_05.png) */}
      <FloatingAnalysisCard
        isOpen={isAnalysisOpen}
        onClose={() => setIsAnalysisOpen(false)}
        onSelectProgramme={handleSelectProgrammeFromAnalysis}
      />

      {/* Floating Command Console at Bottom Center (Matching frame_01.png, frame_05.png, frame_21.png) */}
      <FloatingCommandConsole
        isAnalysisOpen={isAnalysisOpen}
        onToggleAnalysis={() => setIsAnalysisOpen(!isAnalysisOpen)}
        onSearch={(q) => setSearchFilter(q)}
        profile={profile}
        onSelectPreset={onSelectPreset}
        eligibleRate={
          evaluations.length > 0
            ? Math.round(
                (evaluations.filter((e) => e.eligibility_status === 'eligible').length /
                  evaluations.length) *
                  100
              )
            : 0
        }
        totalProgrammes={catalogProgrammes.length > 0 ? catalogProgrammes.length : evaluations.length}
        verifiedFactsCount={
          evaluations.reduce((acc, e) => acc + (e.rules_fired?.length || 0), 0) || 120
        }
        affordabilityRate={
          evaluations.length > 0
            ? Math.round(
                (evaluations.filter((e) => e.affordability?.is_affordable === true).length /
                  evaluations.length) *
                  100
              )
            : 0
        }
      />

      {/* Right Inspector Panel Drawer (Matching frame_15.png) */}
      <RightInspectorPanel
        isOpen={!!selectedEvaluation}
        onClose={() => {
          setSelectedNode(null);
          setSelectedEvaluation(null);
        }}
        evaluation={selectedEvaluation}
        onExploreDetails={onExploreDetails}
      />
    </div>
  );
};
