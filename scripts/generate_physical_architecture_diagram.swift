#!/usr/bin/env swift

// Swift script that renders the cloud-agnostic physical architecture diagram.
//
// Author: Sarala Biswal

import AppKit
import Foundation

let outputPath = "docs/assets/physical-architecture.png"
let canvasSize = NSSize(width: 1800, height: 1180)

struct Card {
    let rect: NSRect
    let eyebrow: String
    let title: String
    let lines: [String]
    let fill: NSColor
    let stroke: NSColor
}

func color(_ hex: UInt32, alpha: CGFloat = 1.0) -> NSColor {
    let red = CGFloat((hex >> 16) & 0xff) / 255.0
    let green = CGFloat((hex >> 8) & 0xff) / 255.0
    let blue = CGFloat(hex & 0xff) / 255.0
    return NSColor(calibratedRed: red, green: green, blue: blue, alpha: alpha)
}

func drawText(
    _ text: String,
    in rect: NSRect,
    size: CGFloat,
    weight: NSFont.Weight = .regular,
    color textColor: NSColor = color(0x152238),
    alignment: NSTextAlignment = .center
) {
    let paragraph = NSMutableParagraphStyle()
    paragraph.alignment = alignment
    paragraph.lineBreakMode = .byWordWrapping
    paragraph.lineSpacing = 2
    let attributes: [NSAttributedString.Key: Any] = [
        .font: NSFont.systemFont(ofSize: size, weight: weight),
        .foregroundColor: textColor,
        .paragraphStyle: paragraph,
    ]
    (text as NSString).draw(in: rect, withAttributes: attributes)
}

func roundedRect(
    _ rect: NSRect,
    radius: CGFloat,
    fill: NSColor,
    stroke: NSColor,
    lineWidth: CGFloat = 2
) {
    let path = NSBezierPath(roundedRect: rect, xRadius: radius, yRadius: radius)
    fill.setFill()
    path.fill()
    stroke.setStroke()
    path.lineWidth = lineWidth
    path.stroke()
}

func drawCard(_ card: Card) {
    roundedRect(card.rect, radius: 16, fill: card.fill, stroke: card.stroke, lineWidth: 2.1)
    drawText(
        card.eyebrow,
        in: NSRect(x: card.rect.minX + 18, y: card.rect.maxY - 36, width: card.rect.width - 36, height: 18),
        size: 12,
        weight: .bold,
        color: color(0x6c788a),
        alignment: .left
    )
    drawText(
        card.title,
        in: NSRect(x: card.rect.minX + 18, y: card.rect.maxY - 70, width: card.rect.width - 36, height: 30),
        size: 22,
        weight: .bold,
        color: color(0x102033),
        alignment: .left
    )
    for (index, line) in card.lines.enumerated() {
        drawText(
            line,
            in: NSRect(
                x: card.rect.minX + 18,
                y: card.rect.maxY - 100 - CGFloat(index) * 23,
                width: card.rect.width - 36,
                height: 21
            ),
            size: 14,
            weight: .medium,
            color: color(0x43536a),
            alignment: .left
        )
    }
}

func drawPanel(_ rect: NSRect, title: String, subtitle: String, stroke: NSColor, fill: NSColor = color(0xffffff, alpha: 0.78)) {
    roundedRect(rect, radius: 28, fill: fill, stroke: stroke, lineWidth: 2)
    drawText(
        title,
        in: NSRect(x: rect.minX + 28, y: rect.maxY - 48, width: rect.width - 56, height: 26),
        size: 21,
        weight: .bold,
        color: color(0x203753),
        alignment: .left
    )
    drawText(
        subtitle,
        in: NSRect(x: rect.minX + 28, y: rect.maxY - 78, width: rect.width - 56, height: 24),
        size: 14,
        weight: .medium,
        color: color(0x607086),
        alignment: .left
    )
}

func drawPill(_ text: String, rect: NSRect, fill: NSColor, stroke: NSColor) {
    roundedRect(rect, radius: 16, fill: fill, stroke: stroke, lineWidth: 1.5)
    drawText(
        text,
        in: NSRect(x: rect.minX + 14, y: rect.minY + 9, width: rect.width - 28, height: rect.height - 18),
        size: 13,
        weight: .semibold,
        color: color(0x26374d)
    )
}

func drawArrowHead(from start: NSPoint, to end: NSPoint, color lineColor: NSColor) {
    let angle = atan2(end.y - start.y, end.x - start.x)
    let arrowLength: CGFloat = 14
    let arrowAngle: CGFloat = .pi / 7
    let p1 = NSPoint(
        x: end.x - arrowLength * cos(angle - arrowAngle),
        y: end.y - arrowLength * sin(angle - arrowAngle)
    )
    let p2 = NSPoint(
        x: end.x - arrowLength * cos(angle + arrowAngle),
        y: end.y - arrowLength * sin(angle + arrowAngle)
    )
    let path = NSBezierPath()
    path.move(to: end)
    path.line(to: p1)
    path.move(to: end)
    path.line(to: p2)
    lineColor.setStroke()
    path.lineWidth = 3
    path.lineCapStyle = .round
    path.stroke()
}

func drawArrow(points: [NSPoint], color lineColor: NSColor = color(0x65738a), width: CGFloat = 3) {
    guard points.count >= 2 else { return }
    let path = NSBezierPath()
    path.move(to: points[0])
    for point in points.dropFirst() {
        path.line(to: point)
    }
    lineColor.setStroke()
    path.lineWidth = width
    path.lineJoinStyle = .round
    path.lineCapStyle = .round
    path.stroke()
    drawArrowHead(from: points[points.count - 2], to: points[points.count - 1], color: lineColor)
}

let image = NSImage(size: canvasSize)
image.lockFocus()

color(0xf4f7fb).setFill()
NSRect(origin: .zero, size: canvasSize).fill()

drawText(
    "Cloud-Agnostic Physical Architecture",
    in: NSRect(x: 80, y: 1096, width: 1640, height: 46),
    size: 40,
    weight: .bold,
    color: color(0x102033)
)
drawText(
    "Deployable containers, local runtime services, and target cloud managed services for Local, OCI, GCP, and generic Kubernetes profiles.",
    in: NSRect(x: 190, y: 1064, width: 1420, height: 28),
    size: 18,
    weight: .regular,
    color: color(0x526179)
)

drawPanel(
    NSRect(x: 70, y: 635, width: 1660, height: 360),
    title: "Application Runtime",
    subtitle: "Frontend and backend containers stay consistent across profiles; provider factories choose infrastructure.",
    stroke: color(0xcad5e5)
)
drawPanel(
    NSRect(x: 70, y: 110, width: 800, height: 470),
    title: "Local Profile",
    subtitle: "Default developer/demo runtime with no OCI or GCP credentials required.",
    stroke: color(0x9eb0c6),
    fill: color(0xffffff, alpha: 0.82)
)
drawPanel(
    NSRect(x: 930, y: 110, width: 800, height: 470),
    title: "Cloud Deployment Profiles",
    subtitle: "Target managed services remain behind provider adapters and stubs until implemented.",
    stroke: color(0xbfd5df),
    fill: color(0xffffff, alpha: 0.82)
)

let browser = Card(
    rect: NSRect(x: 120, y: 760, width: 190, height: 145),
    eyebrow: "CLIENT",
    title: "Browser",
    lines: ["Sales workbench", "Read-only profile UI"],
    fill: color(0xffffff),
    stroke: color(0xb8c6d8)
)
let frontend = Card(
    rect: NSRect(x: 365, y: 760, width: 250, height: 145),
    eyebrow: "CONTAINER",
    title: "Next.js Frontend",
    lines: ["Port 3000 local", "Static UI build", "Calls FastAPI"],
    fill: color(0xf8fbff),
    stroke: color(0x7cb3e6)
)
let edge = Card(
    rect: NSRect(x: 670, y: 760, width: 235, height: 145),
    eyebrow: "EDGE",
    title: "Ingress / LB",
    lines: ["Local direct call", "OCI LB / API Gateway", "GCP LB / API Gateway"],
    fill: color(0xffffff),
    stroke: color(0xb8c6d8)
)
let backend = Card(
    rect: NSRect(x: 960, y: 760, width: 270, height: 145),
    eyebrow: "CONTAINER",
    title: "FastAPI Backend",
    lines: ["AgentOrchestrator", "MCP engine", "Provider factories"],
    fill: color(0xf6fffb),
    stroke: color(0x76bea8)
)
let workers = Card(
    rect: NSRect(x: 1285, y: 760, width: 290, height: 145),
    eyebrow: "IN-PROCESS",
    title: "Agent + MCP Runtime",
    lines: ["LangGraph or native", "Tool registry", "RAG via MCP"],
    fill: color(0xfffbf1),
    stroke: color(0xe3b45d)
)

for card in [browser, frontend, edge, backend, workers] {
    drawCard(card)
}

drawArrow(points: [NSPoint(x: browser.rect.maxX, y: browser.rect.midY), NSPoint(x: frontend.rect.minX, y: frontend.rect.midY)])
drawArrow(points: [NSPoint(x: frontend.rect.maxX, y: frontend.rect.midY), NSPoint(x: edge.rect.minX, y: edge.rect.midY)])
drawArrow(points: [NSPoint(x: edge.rect.maxX, y: edge.rect.midY), NSPoint(x: backend.rect.minX, y: backend.rect.midY)])
drawArrow(points: [NSPoint(x: backend.rect.maxX, y: backend.rect.midY), NSPoint(x: workers.rect.minX, y: workers.rect.midY)])

drawPill("Docker Compose: frontend + backend + optional Ollama", rect: NSRect(x: 250, y: 670, width: 520, height: 38), fill: color(0xffffff), stroke: color(0x9eb0c6))
drawPill("Kubernetes/Cloud Run/OKE/GKE: same app containers", rect: NSRect(x: 1010, y: 670, width: 560, height: 38), fill: color(0xffffff), stroke: color(0x87c9bd))

let localOllama = Card(
    rect: NSRect(x: 115, y: 355, width: 220, height: 145),
    eyebrow: "LOCAL AI",
    title: "Ollama",
    lines: ["LLM chat", "Embeddings", "localhost:11434"],
    fill: color(0xf7f4ff),
    stroke: color(0xb7a8ee)
)
let localChroma = Card(
    rect: NSRect(x: 365, y: 355, width: 220, height: 145),
    eyebrow: "LOCAL VECTOR",
    title: "ChromaDB",
    lines: ["./chroma_db", "Knowledge vectors", "RAG retrieval"],
    fill: color(0xf8f6ff),
    stroke: color(0xb7a8ee)
)
let localSqlite = Card(
    rect: NSRect(x: 615, y: 355, width: 220, height: 145),
    eyebrow: "LOCAL DATA",
    title: "SQLite",
    lines: ["app_data", "Business state", "Run history"],
    fill: color(0xf6fffb),
    stroke: color(0x87c9bd)
)
let localOps = Card(
    rect: NSRect(x: 205, y: 170, width: 250, height: 145),
    eyebrow: "LOCAL PLATFORM",
    title: "Local FS + Env",
    lines: ["Object files", "Environment secrets", "Python logging"],
    fill: color(0xf8fbff),
    stroke: color(0x8eb7de)
)
let localMocks = Card(
    rect: NSRect(x: 485, y: 170, width: 250, height: 145),
    eyebrow: "LOCAL TOOLS",
    title: "Mock Systems",
    lines: ["Salesforce mock", "Oracle CPQ mock", "No cloud creds"],
    fill: color(0xfffbf1),
    stroke: color(0xe3b45d)
)

for card in [localOllama, localChroma, localSqlite, localOps, localMocks] {
    drawCard(card)
}

let oci = Card(
    rect: NSRect(x: 975, y: 355, width: 220, height: 145),
    eyebrow: "OCI",
    title: "OCI Services",
    lines: ["OKE / Compute", "Generative AI", "Object Storage"],
    fill: color(0xfffbf1),
    stroke: color(0xd29a4a)
)
let oracleData = Card(
    rect: NSRect(x: 1225, y: 355, width: 220, height: 145),
    eyebrow: "OCI DATA",
    title: "Oracle Data",
    lines: ["Autonomous DB", "Oracle DB 23ai", "OCI OpenSearch"],
    fill: color(0xfffbf1),
    stroke: color(0xd29a4a)
)
let gcp = Card(
    rect: NSRect(x: 1475, y: 355, width: 220, height: 145),
    eyebrow: "GCP",
    title: "GCP Services",
    lines: ["Cloud Run / GKE", "Vertex AI", "Cloud Storage"],
    fill: color(0xf8fbff),
    stroke: color(0x6da8df)
)
let gcpData = Card(
    rect: NSRect(x: 1065, y: 170, width: 250, height: 145),
    eyebrow: "GCP DATA",
    title: "Google Data",
    lines: ["Cloud SQL", "AlloyDB", "Vertex Vector Search"],
    fill: color(0xf8fbff),
    stroke: color(0x6da8df)
)
let commonCloud = Card(
    rect: NSRect(x: 1345, y: 170, width: 250, height: 145),
    eyebrow: "PLATFORM",
    title: "Ops Providers",
    lines: ["Vault / Secret Manager", "Cloud logging", "OpenTelemetry"],
    fill: color(0xf6fffb),
    stroke: color(0x77b693)
)

for card in [oci, oracleData, gcp, gcpData, commonCloud] {
    drawCard(card)
}

drawArrow(points: [NSPoint(x: backend.rect.midX, y: backend.rect.minY), NSPoint(x: backend.rect.midX, y: 610), NSPoint(x: 470, y: 610), NSPoint(x: 470, y: localOllama.rect.maxY)], color: color(0x66758a))
drawArrow(points: [NSPoint(x: backend.rect.midX, y: backend.rect.minY), NSPoint(x: backend.rect.midX, y: 610), NSPoint(x: 1340, y: 610), NSPoint(x: 1340, y: oci.rect.maxY)], color: color(0x66758a))

drawPill("Local default: PLATFORM_PROFILE=local", rect: NSRect(x: 300, y: 585, width: 420, height: 36), fill: color(0xffffff), stroke: color(0x9eb0c6))
drawPill("Cloud targets: PLATFORM_PROFILE=oci | gcp | generic-kubernetes", rect: NSRect(x: 1115, y: 585, width: 520, height: 36), fill: color(0xffffff), stroke: color(0xbfd5df))

drawText(
    "Physical invariant: app containers can move between local Docker, OCI, GCP, and Kubernetes, but provider-specific SDKs stay inside future adapters.",
    in: NSRect(x: 150, y: 55, width: 1500, height: 28),
    size: 17,
    weight: .semibold,
    color: color(0x27364a)
)

image.unlockFocus()

guard let tiff = image.tiffRepresentation,
      let bitmap = NSBitmapImageRep(data: tiff),
      let png = bitmap.representation(using: .png, properties: [:])
else {
    fatalError("Unable to render physical architecture diagram.")
}

try FileManager.default.createDirectory(
    at: URL(fileURLWithPath: outputPath).deletingLastPathComponent(),
    withIntermediateDirectories: true
)
try png.write(to: URL(fileURLWithPath: outputPath))
print("Generated \(outputPath)")
