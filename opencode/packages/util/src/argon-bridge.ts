import dgram from "node:dgram"
import { spawn } from "node:child_process"
import path from "node:path"
import fs from "node:fs"
import os from "node:os"
import zlib from "node:zlib"
import crypto from "node:crypto"
import { fileURLToPath } from "node:url"
import { EMBEDDED_MASCOT_GZ_BASE64, EMBEDDED_MASCOT_SHA256 } from "./argon-embedded.gen.ts"

const UDP_HOST = "127.0.0.1"
const UDP_PORT = 51515

let sharedSocket: dgram.Socket | undefined
let bugStarted = false

function getSharedSocket(): dgram.Socket {
  if (!sharedSocket) {
    sharedSocket = dgram.createSocket("udp4")
    sharedSocket.unref()
    sharedSocket.on("error", () => {
      // Ignore UDP errors silently
    })
  }
  return sharedSocket
}

export function emitArgonState(state: string, detail: string = ""): void {
  try {
    const message = Buffer.from(JSON.stringify({ state, detail }))
    const socket = getSharedSocket()
    socket.ref()
    socket.send(message, UDP_PORT, UDP_HOST, () => {
      socket.unref()
    })
  } catch {
    // Non-blocking catch to ensure OpenCode is never affected
  }
}

export function extractEmbeddedMascot(): string | undefined {
  if (process.platform !== "win32") return undefined
  if (!EMBEDDED_MASCOT_GZ_BASE64 || !EMBEDDED_MASCOT_SHA256) return undefined

  try {
    const targetDir = path.join(os.homedir(), ".opencode", "bin")
    const targetFile = path.join(targetDir, "argon_bug.exe")

    // Check if target already exists with matching SHA-256
    if (fs.existsSync(targetFile)) {
      try {
        const existingBuf = fs.readFileSync(targetFile)
        const existingSha = crypto.createHash("sha256").update(existingBuf).digest("hex")
        if (existingSha === EMBEDDED_MASCOT_SHA256) {
          return targetFile
        }
      } catch {
        // Fall through to re-extract
      }
    }

    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true })
    }

    const compressed = Buffer.from(EMBEDDED_MASCOT_GZ_BASE64, "base64")
    const decompressed = zlib.gunzipSync(compressed)

    const tempFile = path.join(targetDir, `argon_bug_${Date.now()}.tmp`)
    fs.writeFileSync(tempFile, decompressed)
    try {
      fs.renameSync(tempFile, targetFile)
    } catch {
      fs.copyFileSync(tempFile, targetFile)
      try {
        fs.unlinkSync(tempFile)
      } catch {
        // Ignore temp cleanup error
      }
    }

    return targetFile
  } catch {
    return undefined
  }
}

function resolveMascotScript(): string | undefined {
  try {
    if (process.env.OPENCODE_ARGON_PATH && fs.existsSync(process.env.OPENCODE_ARGON_PATH)) {
      return process.env.OPENCODE_ARGON_PATH
    }

    const currentDir =
      typeof import.meta.dirname === "string"
        ? import.meta.dirname
        : path.dirname(fileURLToPath(import.meta.url))

    const repoRoot = path.resolve(currentDir, "../../..")

    const candidatePaths = [
      path.join(repoRoot, "argon_bug", "main.py"),
      path.resolve(process.cwd(), "argon_bug", "main.py"),
      path.resolve(process.cwd(), "..", "argon_bug", "main.py"),
      path.resolve(process.cwd(), "opencode", "argon_bug", "main.py"),
    ]

    return candidatePaths.find((p) => fs.existsSync(p))
  } catch {
    return undefined
  }
}

function getPythonExecutable(): string {
  if (process.env.PYTHON_PATH) {
    return process.env.PYTHON_PATH
  }
  return process.platform === "win32" ? "python" : "python3"
}

function getMascotArgs(): string[] {
  const args = ["--parent-pid", String(process.pid)]
  if (process.env.OPENCODE_ARGON_LANG) {
    args.push("--lang", process.env.OPENCODE_ARGON_LANG)
  }
  return args
}

function launchBinary(exePath: string): boolean {
  try {
    const child = spawn(exePath, getMascotArgs(), {
      detached: false,
      stdio: "ignore",
      windowsHide: true,
    })
    child.on("error", () => {
      // Ignore binary spawn error
    })
    child.unref()
    bugStarted = true
    emitArgonState("IDLE")
    return true
  } catch {
    return false
  }
}

export function startArgonBug(): void {
  if (process.env.OPENCODE_NO_MASCOT === "1") return
  if (bugStarted) return

  try {
    // Priority 1: User explicitly provided path to executable
    if (process.env.OPENCODE_ARGON_EXE && fs.existsSync(process.env.OPENCODE_ARGON_EXE)) {
      if (launchBinary(process.env.OPENCODE_ARGON_EXE)) return
    }

    // Priority 2: Embedded binary extracted to ~/.opencode/bin/argon_bug.exe
    const extractedExe = extractEmbeddedMascot()
    if (extractedExe && launchBinary(extractedExe)) {
      return
    }

    // Priority 3: Dev-mode fallback to python script
    const scriptPath = resolveMascotScript()
    if (!scriptPath) {
      return
    }

    const pythonBin = getPythonExecutable()
    const child = spawn(pythonBin, [scriptPath, ...getMascotArgs()], {
      detached: true,
      stdio: "ignore",
      windowsHide: true,
    })

    child.on("error", () => {
      // Gracefully ignore spawn errors (e.g. python not found)
    })

    child.unref()
    bugStarted = true

    // Initial IDLE state
    emitArgonState("IDLE")
  } catch {
    // Silently continue so OpenCode startup is never blocked
  }
}

export function stopArgonBug(): void {
  emitArgonState("QUIT")
  if (sharedSocket) {
    try {
      sharedSocket.close()
    } catch {
      // Ignore socket close error
    }
    sharedSocket = undefined
  }
  bugStarted = false
}
