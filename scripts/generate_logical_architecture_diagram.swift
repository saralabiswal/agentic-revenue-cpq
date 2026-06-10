#!/usr/bin/env swift

// Swift script that renders the cloud-agnostic logical architecture diagram.
//
// Author: Sarala Biswal

import AppKit
import Foundation

let outputPath = "docs/assets/logical-architecture.png"
let canvasSize = NSSize(width: 1800, height: 1180)

struct Box {
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

func drawBox(_ box: Box) {
    roundedRect(box.rect, radius: 18, fill: box.fill, stroke: box.stroke, lineWidth: 2.2)
    drawText(
        box.eyebrow,
        in: NSRect(x: box.rect.minX + 22, y: box.rect.maxY - 40, width: box.rect.width - 44, height: 20),
        size: 12,
        weight: .bold,
        color: color(0x68768a),
        alignment: .left
    )
    drawText(
        box.title,
        in: NSRect(x: box.rect.minX + 22, y: box.rect.maxY - 76, width: box.rect.width - 44, height: 32),
        size: 24,
        weight: .bold,
        color: color(0x112238),
        alignment: .left
    )

    for (index, line) in box.lines.enumerated() {
        drawText(
            line,
            in: NSRect(
                x: box.rect.minX + 22,
                y: box.rect.maxY - 108 - CGFloat(index) * 24,
                width: box.rect.width - 44,
                height: 22
            ),
            size: 15,
            weight: .medium,
            color: color(0x41516a),
            alignment: .left
        )
    }
}

func drawPanel(_ rect: NSRect, title: String, subtitle: String, stroke: NSColor) {
    roundedRect(rect, radius: 28, fill: color(0xffffff, alpha: 0.78), stroke: stroke, lineWidth: 2)
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
        in: NSRect(x: rect.minX + 16, y: rect.minY + 9, width: rect.width - 32, height: rect.height - 18),
        size: 14,
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

func drawArrow(points: [NSPoint], color lineColor: NSColor = color(0x66758a), width: CGFloat = 3) {
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

func drawDot(_ center: NSPoint, text: String, fill: NSColor) {
    let rect = NSRect(x: center.x - 17, y: center.y - 17, width: 34, height: 34)
    let path = NSBezierPath(ovalIn: rect)
    fill.setFill()
    path.fill()
    color(0xffffff).setStroke()
    path.lineWidth = 3
    path.stroke()
    drawText(text, in: NSRect(x: rect.minX, y: rect.minY + 8, width: rect.width, height: 17), size: 13, weight: .bold, color: color(0xffffff))
}

let image = NSImage(size: canvasSize)
image.lockFocus()

color(0xf4f7fb).setFill()
NSRect(origin: .zero, size: canvasSize).fill()

drawText(
    "Cloud-Agnostic Logical Architecture",
    in: NSRect(x: 80, y: 1096, width: 1640, height: 46),
    size: 40,
    weight: .bold,
    color: color(0x102033)
)
drawText(
    "A stable application core: AgentOrchestrator controls workflow, internal MCP controls execution, official MCP stdio exposes read-only tools, and RAG stays behind search_knowledge.",
    in: NSRect(x: 170, y: 1064, width: 1460, height: 28),
    size: 18,
    weight: .regular,
    color: color(0x526179)
)

drawPill("No direct agent imports of integrations, vector stores, cloud SDKs, or official MCP transport code", rect: NSRect(x: 390, y: 1010, width: 1020, height: 38), fill: color(0xeaf8f6), stroke: color(0x87c9bd))

let appPanel = NSRect(x: 70, y: 585, width: 1660, height: 380)
let providerPanel = NSRect(x: 70, y: 100, width: 1660, height: 430)

drawPanel(
    appPanel,
    title: "Application Core",
    subtitle: "These contracts remain stable when PLATFORM_PROFILE changes.",
    stroke: color(0xcad5e5)
)
drawPanel(
    providerPanel,
    title: "Provider Layer",
    subtitle: "Local providers are implemented today. OCI, GCP, and Kubernetes mappings are selected by config and remain adapter boundaries.",
    stroke: color(0xbfd5df)
)

let user = Box(
    rect: NSRect(x: 105, y: 700, width: 195, height: 165),
    eyebrow: "USER",
    title: "Sales Rep",
    lines: ["Review", "Select", "Approve"],
    fill: color(0xffffff),
    stroke: color(0xb8c6d8)
)
let frontend = Box(
    rect: NSRect(x: 350, y: 700, width: 230, height: 165),
    eyebrow: "UI",
    title: "Next.js",
    lines: ["Business view", "Architecture view", "Developer view"],
    fill: color(0xf8fbff),
    stroke: color(0x7cb3e6)
)
let api = Box(
    rect: NSRect(x: 630, y: 700, width: 230, height: 165),
    eyebrow: "API",
    title: "FastAPI",
    lines: ["Routes", "Schemas", "Runtime profile"],
    fill: color(0xffffff),
    stroke: color(0x87c9bd)
)
let orchestrator = Box(
    rect: NSRect(x: 910, y: 700, width: 280, height: 165),
    eyebrow: "AGENT",
    title: "AgentOrchestrator",
    lines: ["LangGraph local/demo", "Native Python prod-safe", "Cloud agents are stubs"],
    fill: color(0xf6fffb),
    stroke: color(0x76bea8)
)
let mcp = Box(
    rect: NSRect(x: 1215, y: 700, width: 255, height: 165),
    eyebrow: "EXECUTION",
    title: "Internal MCP",
    lines: ["Registered tools", "Payload validation", "Tool traces"],
    fill: color(0xfffbf1),
    stroke: color(0xe3b45d)
)
let mcpClient = Box(
    rect: NSRect(x: 1510, y: 700, width: 185, height: 165),
    eyebrow: "CLIENT",
    title: "MCP Client",
    lines: ["Inspector", "IDE", "Claude"],
    fill: color(0xffffff),
    stroke: color(0xe3b45d)
)

let llm = Box(
    rect: NSRect(x: 910, y: 560, width: 280, height: 125),
    eyebrow: "REASONING",
    title: "LLMClient",
    lines: ["Ollama local, cloud stubs"],
    fill: color(0xf7f4ff),
    stroke: color(0xb7a8ee)
)
let officialMcp = Box(
    rect: NSRect(x: 1215, y: 560, width: 280, height: 125),
    eyebrow: "OFFICIAL MCP",
    title: "Stdio Server",
    lines: ["FastMCP adapter", "Contracts, policy, audit"],
    fill: color(0xfffbf1),
    stroke: color(0xe3b45d)
)
let tools = Box(
    rect: NSRect(x: 235, y: 270, width: 275, height: 170),
    eyebrow: "TOOLS",
    title: "Integrations",
    lines: ["Salesforce access", "Oracle CPQ access", "All calls via MCP"],
    fill: color(0xffffff),
    stroke: color(0x8eb7de)
)
let rag = Box(
    rect: NSRect(x: 575, y: 270, width: 275, height: 170),
    eyebrow: "KNOWLEDGE",
    title: "RAG Service",
    lines: ["search_knowledge only", "EmbeddingClient", "VectorStore"],
    fill: color(0xf8f6ff),
    stroke: color(0xb7a8ee)
)
let business = Box(
    rect: NSRect(x: 915, y: 270, width: 275, height: 170),
    eyebrow: "STATE",
    title: "BusinessStore",
    lines: ["Accounts / opportunities", "Quotes / orders", "Source-prefixed IDs"],
    fill: color(0xf6fffb),
    stroke: color(0x87c9bd)
)
let platform = Box(
    rect: NSRect(x: 1255, y: 270, width: 275, height: 170),
    eyebrow: "PLATFORM",
    title: "Platform Providers",
    lines: ["ObjectStore", "SecretsProvider", "ObservabilityProvider"],
    fill: color(0xf8fbff),
    stroke: color(0x8eb7de)
)

drawArrow(points: [NSPoint(x: user.rect.maxX - 6, y: user.rect.midY), NSPoint(x: frontend.rect.minX + 6, y: frontend.rect.midY)])
drawArrow(points: [NSPoint(x: frontend.rect.maxX - 6, y: frontend.rect.midY), NSPoint(x: api.rect.minX + 6, y: api.rect.midY)])
drawArrow(points: [NSPoint(x: api.rect.maxX - 6, y: api.rect.midY), NSPoint(x: orchestrator.rect.minX + 6, y: orchestrator.rect.midY)])
drawArrow(points: [NSPoint(x: orchestrator.rect.maxX - 6, y: orchestrator.rect.midY), NSPoint(x: mcp.rect.minX + 6, y: mcp.rect.midY)])
drawArrow(points: [NSPoint(x: mcpClient.rect.midX, y: mcpClient.rect.minY), NSPoint(x: mcpClient.rect.midX, y: officialMcp.rect.midY), NSPoint(x: officialMcp.rect.maxX - 6, y: officialMcp.rect.midY)], color: color(0xb57918))
drawArrow(points: [NSPoint(x: orchestrator.rect.midX - 35, y: orchestrator.rect.minY + 6), NSPoint(x: llm.rect.midX - 35, y: llm.rect.maxY - 6)], color: color(0x8d76dd))
drawArrow(points: [NSPoint(x: llm.rect.midX + 35, y: llm.rect.maxY - 6), NSPoint(x: orchestrator.rect.midX + 35, y: orchestrator.rect.minY + 6)], color: color(0x8d76dd))
drawArrow(points: [NSPoint(x: officialMcp.rect.midX, y: officialMcp.rect.minY), NSPoint(x: officialMcp.rect.midX, y: 545), NSPoint(x: rag.rect.midX, y: 545), NSPoint(x: rag.rect.midX, y: rag.rect.maxY)], color: color(0xb57918))

drawArrow(points: [NSPoint(x: mcp.rect.midX, y: mcp.rect.minY), NSPoint(x: mcp.rect.midX, y: 545), NSPoint(x: tools.rect.midX, y: 545), NSPoint(x: tools.rect.midX, y: tools.rect.maxY)])
drawArrow(points: [NSPoint(x: mcp.rect.midX, y: mcp.rect.minY), NSPoint(x: mcp.rect.midX, y: 545), NSPoint(x: rag.rect.midX, y: 545), NSPoint(x: rag.rect.midX, y: rag.rect.maxY)], color: color(0x8d76dd))
drawArrow(points: [NSPoint(x: mcp.rect.midX, y: mcp.rect.minY), NSPoint(x: mcp.rect.midX, y: 545), NSPoint(x: business.rect.midX, y: 545), NSPoint(x: business.rect.midX, y: business.rect.maxY)], color: color(0x4f8f7c))
drawArrow(points: [NSPoint(x: mcp.rect.midX, y: mcp.rect.minY), NSPoint(x: mcp.rect.midX, y: 545), NSPoint(x: platform.rect.midX, y: 545), NSPoint(x: platform.rect.midX, y: platform.rect.maxY)], color: color(0x668cb8))

// Draw cards after connectors so lines never cross labels inside boxes.
for box in [user, frontend, api, orchestrator, mcp, mcpClient, llm, officialMcp, tools, rag, business, platform] {
    drawBox(box)
}

drawDot(NSPoint(x: 325, y: user.rect.midY), text: "1", fill: color(0x52749a))
drawDot(NSPoint(x: 605, y: api.rect.midY), text: "2", fill: color(0x2f9277))
drawDot(NSPoint(x: 1215, y: mcp.rect.midY), text: "3", fill: color(0xb57918))
drawDot(NSPoint(x: mcp.rect.midX, y: 545), text: "4", fill: color(0x576a82))

drawPill("Local: LangGraph + Ollama + ChromaDB + SQLite + local_fs + env + Python logging", rect: NSRect(x: 135, y: 230, width: 720, height: 38), fill: color(0xffffff), stroke: color(0x9eb0c6))
drawPill("OCI: Native / Responses API + OCI GenAI + DB 23ai + Autonomous DB + Object Storage + Vault", rect: NSRect(x: 945, y: 230, width: 720, height: 38), fill: color(0xffffff), stroke: color(0xd29a4a))
drawPill("GCP: Native / Vertex Agent + Gemini + Vector Search + Cloud SQL / AlloyDB", rect: NSRect(x: 135, y: 172, width: 720, height: 38), fill: color(0xffffff), stroke: color(0x6da8df))
drawPill("Generic Kubernetes: Native + configured LLM + pgvector/OpenSearch + PostgreSQL", rect: NSRect(x: 945, y: 172, width: 720, height: 38), fill: color(0xffffff), stroke: color(0x77b693))

drawText(
    "Invariant: PLATFORM_PROFILE can change providers, but API payload names, MCP tool names, RAG access, and source-owned IDs remain stable.",
    in: NSRect(x: 170, y: 52, width: 1460, height: 28),
    size: 17,
    weight: .semibold,
    color: color(0x27364a)
)

image.unlockFocus()

guard let tiff = image.tiffRepresentation,
      let bitmap = NSBitmapImageRep(data: tiff),
      let png = bitmap.representation(using: .png, properties: [:])
else {
    fatalError("Unable to render logical architecture diagram.")
}

try FileManager.default.createDirectory(
    at: URL(fileURLWithPath: outputPath).deletingLastPathComponent(),
    withIntermediateDirectories: true
)
try png.write(to: URL(fileURLWithPath: outputPath))
print("Generated \(outputPath)")
