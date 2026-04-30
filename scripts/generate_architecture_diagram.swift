#!/usr/bin/env swift

import AppKit
import Foundation

let outputPath = "docs/assets/architecture.png"
let canvasSize = NSSize(width: 1800, height: 1120)

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

func drawSoftPanel(_ rect: NSRect, title: String, subtitle: String, stroke: NSColor, labelColor: NSColor) {
    roundedRect(rect, radius: 26, fill: color(0xffffff, alpha: 0.74), stroke: stroke, lineWidth: 2)
    drawText(
        title,
        in: NSRect(x: rect.minX + 34, y: rect.maxY - 50, width: 360, height: 28),
        size: 21,
        weight: .bold,
        color: labelColor,
        alignment: .left
    )
    drawText(
        subtitle,
        in: NSRect(x: rect.minX + 34, y: rect.maxY - 82, width: rect.width - 68, height: 26),
        size: 15,
        weight: .medium,
        color: color(0x536278),
        alignment: .left
    )
}

func drawCard(_ card: Card) {
    roundedRect(card.rect, radius: 16, fill: card.fill, stroke: card.stroke, lineWidth: 2.2)

    drawText(
        card.eyebrow,
        in: NSRect(x: card.rect.minX + 22, y: card.rect.maxY - 38, width: card.rect.width - 44, height: 20),
        size: 13,
        weight: .semibold,
        color: color(0x647086),
        alignment: .left
    )
    drawText(
        card.title,
        in: NSRect(x: card.rect.minX + 22, y: card.rect.maxY - 72, width: card.rect.width - 44, height: 30),
        size: 24,
        weight: .bold,
        color: color(0x102033),
        alignment: .left
    )

    let lineGap: CGFloat = 23
    let defaultLineStart = card.rect.maxY - 102
    let minLastLineY = card.rect.minY + 16
    let lineSpan = CGFloat(max(card.lines.count - 1, 0)) * lineGap
    let lineStart = max(defaultLineStart, minLastLineY + lineSpan)
    for (index, line) in card.lines.enumerated() {
        drawText(
            line,
            in: NSRect(
                x: card.rect.minX + 22,
                y: lineStart - CGFloat(index) * lineGap,
                width: card.rect.width - 44,
                height: 21
            ),
            size: 15,
            weight: .regular,
            color: color(0x405068),
            alignment: .left
        )
    }
}

func drawPill(_ text: String, rect: NSRect, fill: NSColor, stroke: NSColor) {
    roundedRect(rect, radius: 15, fill: fill, stroke: stroke, lineWidth: 1.5)
    drawText(
        text,
        in: NSRect(x: rect.minX + 16, y: rect.minY + 9, width: rect.width - 32, height: rect.height - 18),
        size: 15,
        weight: .semibold,
        color: color(0x243248)
    )
}

func drawArrowHead(from start: NSPoint, to end: NSPoint, color lineColor: NSColor) {
    let angle = atan2(end.y - start.y, end.x - start.x)
    let arrowLength: CGFloat = 15
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

func drawDot(_ center: NSPoint, fill: NSColor, text: String) {
    let rect = NSRect(x: center.x - 18, y: center.y - 18, width: 36, height: 36)
    let path = NSBezierPath(ovalIn: rect)
    fill.setFill()
    path.fill()
    color(0xffffff).setStroke()
    path.lineWidth = 3
    path.stroke()
    drawText(text, in: NSRect(x: rect.minX, y: rect.minY + 8, width: rect.width, height: 18), size: 14, weight: .bold, color: color(0xffffff))
}

let image = NSImage(size: canvasSize)
image.lockFocus()

color(0xf5f7fb).setFill()
NSRect(origin: .zero, size: canvasSize).fill()

drawText(
    "Enterprise AI Agent Platform",
    in: NSRect(x: 80, y: 1038, width: 1640, height: 46),
    size: 40,
    weight: .bold,
    color: color(0x102033)
)
drawText(
    "A governed agentic command center between Salesforce CRM and Oracle CPQ, with LangGraph planning, LLM reasoning, MCP execution, and full traceability.",
    in: NSRect(x: 220, y: 1004, width: 1360, height: 28),
    size: 18,
    weight: .regular,
    color: color(0x526179)
)

drawPill("LLM: reasoning only", rect: NSRect(x: 410, y: 948, width: 220, height: 38), fill: color(0xeaf1ff), stroke: color(0xa6bff1))
drawPill("Agent: orchestration", rect: NSRect(x: 660, y: 948, width: 230, height: 38), fill: color(0xe9f7ef), stroke: color(0x95cda8))
drawPill("MCP: execution boundary", rect: NSRect(x: 920, y: 948, width: 270, height: 38), fill: color(0xfff3d9), stroke: color(0xe3b45d))
drawPill("Tools: system integrations", rect: NSRect(x: 1220, y: 948, width: 280, height: 38), fill: color(0xf0ecff), stroke: color(0xb8a8ed))

let platformPanel = NSRect(x: 340, y: 565, width: 1380, height: 350)
let mcpPanel = NSRect(x: 80, y: 130, width: 1640, height: 390)

drawSoftPanel(
    platformPanel,
    title: "Agentic Orchestration App",
    subtitle: "User experience, API state, agent planning, and grounded responses live here.",
    stroke: color(0xcad5e5),
    labelColor: color(0x1c3556)
)
drawSoftPanel(
    mcpPanel,
    title: "MCP Execution Boundary",
    subtitle: "The agent reaches Salesforce, RAG, and Oracle CPQ only through registered tools.",
    stroke: color(0xe1ad45),
    labelColor: color(0x5a3b00)
)

let salesRep = Card(
    rect: NSRect(x: 80, y: 660, width: 230, height: 170),
    eyebrow: "USER",
    title: "Sales Rep",
    lines: ["Command", "Review", "Select"],
    fill: color(0xffffff),
    stroke: color(0xb6c2d2)
)
let workbench = Card(
    rect: NSRect(x: 410, y: 660, width: 300, height: 170),
    eyebrow: "FRONTEND",
    title: "Next.js Workbench",
    lines: ["Opportunity context", "Command assistant", "Architecture trace"],
    fill: color(0xffffff),
    stroke: color(0x77a9d9)
)
let backend = Card(
    rect: NSRect(x: 780, y: 660, width: 300, height: 170),
    eyebrow: "API + DATA",
    title: "FastAPI Backend",
    lines: ["REST API", "SQLite business data", "Agent run history"],
    fill: color(0xffffff),
    stroke: color(0x78c6ad)
)
let agent = Card(
    rect: NSRect(x: 1150, y: 660, width: 300, height: 170),
    eyebrow: "ORCHESTRATION",
    title: "LangGraph Agent",
    lines: ["Analyze intent", "Retrieve context", "Plan next action"],
    fill: color(0xffffff),
    stroke: color(0x78c6ad)
)
let llm = Card(
    rect: NSRect(x: 1150, y: 520, width: 300, height: 128),
    eyebrow: "REASONING",
    title: "LLMClient",
    lines: ["Ollama or fallback", "Grounded response only"],
    fill: color(0xffffff),
    stroke: color(0xb8a8ed)
)
let router = Card(
    rect: NSRect(x: 660, y: 320, width: 480, height: 108),
    eyebrow: "MCP",
    title: "Tool Registry + Engine",
    lines: ["Validate request, execute tool, return trace"],
    fill: color(0xfffbf1),
    stroke: color(0xe1ad45)
)
let salesforce = Card(
    rect: NSRect(x: 160, y: 140, width: 330, height: 165),
    eyebrow: "CRM SYSTEM",
    title: "Salesforce CRM",
    lines: ["Accounts", "Opportunities", "SF-owned identifiers"],
    fill: color(0xf7fbff),
    stroke: color(0x77a9d9)
)
let rag = Card(
    rect: NSRect(x: 735, y: 140, width: 330, height: 165),
    eyebrow: "KNOWLEDGE SYSTEM",
    title: "RAG Service",
    lines: ["Ollama embeddings", "ChromaDB knowledge", "Search context"],
    fill: color(0xf8f6ff),
    stroke: color(0xb8a8ed)
)
let cpq = Card(
    rect: NSRect(x: 1310, y: 140, width: 330, height: 165),
    eyebrow: "CPQ SYSTEM",
    title: "Oracle CPQ",
    lines: ["Recommendations and pricing", "Quotes and orders", "Oracle-owned identifiers"],
    fill: color(0xfffbf1),
    stroke: color(0xe1ad45)
)

drawArrow(points: [
    NSPoint(x: salesRep.rect.maxX, y: salesRep.rect.midY),
    NSPoint(x: workbench.rect.minX, y: workbench.rect.midY),
])
drawArrow(points: [
    NSPoint(x: workbench.rect.maxX, y: workbench.rect.midY),
    NSPoint(x: backend.rect.minX, y: backend.rect.midY),
])
drawArrow(points: [
    NSPoint(x: backend.rect.maxX, y: backend.rect.midY),
    NSPoint(x: agent.rect.minX, y: agent.rect.midY),
])
drawArrow(points: [
    NSPoint(x: agent.rect.midX - 28, y: agent.rect.minY),
    NSPoint(x: agent.rect.midX - 28, y: llm.rect.maxY),
], color: color(0x8b76d8))
drawArrow(points: [
    NSPoint(x: llm.rect.midX + 28, y: llm.rect.maxY),
    NSPoint(x: llm.rect.midX + 28, y: agent.rect.minY),
], color: color(0x8b76d8))
drawArrow(points: [
    NSPoint(x: agent.rect.midX, y: llm.rect.minY),
    NSPoint(x: agent.rect.midX, y: 485),
    NSPoint(x: router.rect.midX, y: 485),
    NSPoint(x: router.rect.midX, y: router.rect.maxY),
], color: color(0x5a6b82), width: 3.5)
drawArrow(points: [
    NSPoint(x: router.rect.midX, y: router.rect.minY),
    NSPoint(x: router.rect.midX, y: 330),
    NSPoint(x: salesforce.rect.midX, y: 330),
    NSPoint(x: salesforce.rect.midX, y: salesforce.rect.maxY),
], color: color(0x5a6b82))
drawArrow(points: [
    NSPoint(x: router.rect.midX, y: router.rect.minY),
    NSPoint(x: router.rect.midX, y: rag.rect.maxY),
], color: color(0x8b76d8))
drawArrow(points: [
    NSPoint(x: router.rect.midX, y: router.rect.minY),
    NSPoint(x: router.rect.midX, y: 330),
    NSPoint(x: cpq.rect.midX, y: 330),
    NSPoint(x: cpq.rect.midX, y: cpq.rect.maxY),
], color: color(0x5a6b82))

for card in [salesRep, workbench, backend, agent, llm, router, salesforce, rag, cpq] {
    drawCard(card)
}

drawDot(NSPoint(x: 360, y: salesRep.rect.midY), fill: color(0x496d95), text: "1")
drawDot(NSPoint(x: 740, y: backend.rect.midY), fill: color(0x2f8c70), text: "2")
drawDot(NSPoint(x: 1115, y: agent.rect.midY), fill: color(0x2f8c70), text: "3")
drawDot(NSPoint(x: router.rect.midX, y: 485), fill: color(0xb57918), text: "4")

drawText(
    "Business flow: Salesforce Account -> Salesforce Opportunity -> Agent Recommendation -> Oracle CPQ Quote -> Oracle CPQ Order",
    in: NSRect(x: 150, y: 80, width: 1500, height: 30),
    size: 18,
    weight: .semibold,
    color: color(0x27364a)
)
drawText(
    "Ownership rule: Salesforce owns account and opportunity IDs. Oracle CPQ owns quote and order IDs. The platform owns orchestration state and execution trace.",
    in: NSRect(x: 170, y: 48, width: 1460, height: 24),
    size: 15,
    weight: .medium,
    color: color(0x647086)
)

image.unlockFocus()

guard let tiff = image.tiffRepresentation,
      let bitmap = NSBitmapImageRep(data: tiff),
      let png = bitmap.representation(using: .png, properties: [:])
else {
    fatalError("Unable to render architecture diagram.")
}

try FileManager.default.createDirectory(
    at: URL(fileURLWithPath: outputPath).deletingLastPathComponent(),
    withIntermediateDirectories: true
)
try png.write(to: URL(fileURLWithPath: outputPath))
print("Generated \(outputPath)")
