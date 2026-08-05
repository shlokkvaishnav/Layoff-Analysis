"use client";

import { Canvas } from "@react-three/fiber";
import { Float, MeshDistortMaterial, Sphere } from "@react-three/drei";
import { useMemo } from "react";
import { useTheme } from "@/lib/theme";

function DistortedCore({ color }: { color: string }) {
  return (
    <Float speed={1.1} rotationIntensity={0.5} floatIntensity={1.1}>
      <Sphere args={[1.6, 128, 128]}>
        <MeshDistortMaterial
          color={color}
          attach="material"
          distort={0.42}
          speed={1.4}
          roughness={0.2}
          metalness={0.25}
        />
      </Sphere>
    </Float>
  );
}

// Deterministic scatter, not Math.random() -- React flags RNG calls during render.
function scatterPosition(i: number): [number, number, number] {
  const a = i * 2.399963; // golden-angle-ish step for a non-repeating-looking spread
  return [
    Math.sin(a) * 4.5 * ((i % 7) / 6 + 0.3),
    Math.cos(a * 1.3) * 3,
    Math.sin(a * 0.7) * 3 - 1,
  ];
}

function DataMotes({ color }: { color: string }) {
  const positions = useMemo(
    () => Array.from({ length: 48 }, (_, i) => scatterPosition(i)),
    [],
  );
  return (
    <>
      {positions.map((p, i) => (
        <mesh key={i} position={p}>
          <sphereGeometry args={[0.015 + (i % 3) * 0.01, 8, 8]} />
          <meshBasicMaterial color={color} transparent opacity={0.55} />
        </mesh>
      ))}
    </>
  );
}

// No HDRI/environment map -- deliberately self-contained (no external asset
// fetch at runtime), just ambient + directional + a cool rim light.
export function Hero3D() {
  const { theme } = useTheme();
  const coreColor = theme === "dark" ? "#D2B48C" : "#8B5A2B";
  const moteColor = theme === "dark" ? "#E8CDA3" : "#B8722E";

  return (
    <Canvas
      camera={{ position: [0, 0, 6.5], fov: 42 }}
      dpr={[1, 1.5]}
      gl={{ antialias: true, alpha: true }}
    >
      <ambientLight intensity={0.55} />
      <directionalLight position={[3, 3, 4]} intensity={1.1} color={coreColor} />
      <directionalLight position={[-4, -2, -3]} intensity={0.4} color="#6F4E37" />
      <DistortedCore color={coreColor} />
      <DataMotes color={moteColor} />
    </Canvas>
  );
}
