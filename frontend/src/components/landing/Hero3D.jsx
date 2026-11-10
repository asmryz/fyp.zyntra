/**
 * The rotating 3D "ZYNTRA" heading (React Three Fiber).
 * Loaded lazily by HeroLogo so the rest of the page does not wait for three.js.
 * Users who prefer reduced motion get the static CSS version instead (see HeroLogo).
 */
import { Text3D } from '@react-three/drei'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { useLayoutEffect, useRef } from 'react'

// Only the letters Z Y N T R A (subset of the MgOpen Moderna / "Helvetiker" font)
const FONT_URL = '/fonts/zyntra-3d.typeface.json'
const SECONDS_PER_TURN = 14
// 0 = constant speed. Higher values turn more slowly while the word faces the
// viewer and faster while it faces away, which keeps it readable for longer.
const FRONT_SLOWDOWN = 0.55
// Width of the word in scene units at size 1, used to fit it to the screen
const WORD_WIDTH = 5.6
// A slight downward tilt so the top of the letters is visible
const START_ROTATION = [0.06, 0, 0]

function RotatingWord() {
  const groupRef = useRef(null)
  const textRef = useRef(null)
  const phase = useRef(0)
  const { viewport } = useThree()
  const scale = Math.min(1.3, (viewport.width * 0.9) / WORD_WIDTH)

  // Text geometry starts at its bottom-left corner. Moving the geometry so its
  // middle is at (0, 0, 0) makes the word turn around its own centre.
  // center() does nothing if the geometry is already centred.
  useLayoutEffect(() => {
    textRef.current?.geometry.center()
  })

  useFrame((_, delta) => {
    if (!groupRef.current) return
    // Cap delta so switching tabs does not cause a sudden jump
    phase.current = (phase.current + Math.min(delta, 0.1) / SECONDS_PER_TURN) % 1
    const turn = 2 * Math.PI * phase.current
    // One full 360-degree turn per cycle; the sine term slows it near the front
    groupRef.current.rotation.y = turn - FRONT_SLOWDOWN * Math.sin(turn)
  })

  return (
    <group ref={groupRef} scale={scale} rotation={START_ROTATION}>
      <Text3D
        ref={textRef}
        font={FONT_URL}
        size={1}
        height={0.38}
        letterSpacing={0.05}
        curveSegments={10}
        bevelEnabled
        bevelThickness={0.04}
        bevelSize={0.025}
        bevelSegments={4}
      >
        ZYNTRA
        {/* material-0: front and back faces, material-1: extruded sides */}
        <meshStandardMaterial
          attach="material-0"
          color="#19E8C9"
          emissive="#19E8C9"
          emissiveIntensity={0.12}
          metalness={0.15}
          roughness={0.38}
        />
        <meshStandardMaterial attach="material-1" color="#FF4B3E" metalness={0.35} roughness={0.32} />
      </Text3D>
    </group>
  )
}

export default function Hero3D({ animate }) {
  return (
    <Canvas
      className="hero-canvas"
      camera={{ position: [0, 0, 8], fov: 35 }}
      dpr={[1, 1.75]}
      gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      // Stop drawing completely while the hero is scrolled out of view
      frameloop={animate ? 'always' : 'never'}
    >
      <ambientLight intensity={0.75} />
      <directionalLight position={[2, 3, 8]} intensity={2.4} />
      {/* Warm light directly behind the word: tints the back face as it turns, not the front */}
      <directionalLight position={[0, 1, -8]} intensity={1.1} color="#FF4B3E" />
      <directionalLight position={[0, -4, 3]} intensity={0.5} color="#19E8C9" />
      <RotatingWord />
    </Canvas>
  )
}
