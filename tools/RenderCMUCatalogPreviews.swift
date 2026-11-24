import Foundation
@testable import MessCharacterCreatorApp
import MessCharacterCreatorKit
import Metal
import simd

/// Offline capture uses the same Default Human, shader and framing as Motion Data cards.
@main
struct RenderCMUCatalogPreviews
{
    struct Take: Decodable
    {
        let takeID: String
        let capturedFrames: [Int]
        let posterFrame: Int
        let animationFrames: [Int]
    }

    enum Failure: Error { case badSamples(String), missingInputs }

    static func main() async throws
    {
        let environment = ProcessInfo.processInfo.environment
        guard let inputPath = environment["CMU_PREVIEW_INPUT"] else { throw Failure.missingInputs }
        let inputs = URL(fileURLWithPath: inputPath)
        let output = URL(fileURLWithPath: CommandLine.arguments[2])
        let takes = try JSONDecoder().decode([Take].self, from: Data(contentsOf: inputs.appending(path: "render.json")))
        try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
        let creator = CharacterCreator()
        let human = try await MotionCaptureHuman.prepareDefault(creator)
        let contentPack = try await creator.assetPackSHA256()
        print("Default Human asset pack \(contentPack)")
        try Data((contentPack + "\n").utf8).write(to: output.appending(path: "asset-pack.txt"), options: .atomic)
        let workerCount = max(1, Int(environment["CMU_PREVIEW_WORKERS"] ?? "") ?? 4)
        let failed = await withTaskGroup(of: [String].self, returning: [String].self)
        { group in
            for worker in 0 ..< min(workerCount, takes.count)
            {
                group.addTask
                {
                    let indices = stride(from: worker, to: takes.count, by: workerCount)
                    guard let device = MTLCreateSystemDefaultDevice()
                    else { return indices.map { takes[$0].takeID } }
                    let renderer = CharacterRenderer(device: device)
                    var failed: [String] = []
                    for index in indices
                    {
                        let take = takes[index]
                        let destination = output.appending(path: take.takeID)
                        let marker = destination.appending(path: ".complete")
                        let frameCount = take.animationFrames.count
                        let expected = Data("\(frameCount)\n".utf8)
                        if (try? Data(contentsOf: marker)) == expected { continue }
                        do
                        {
                            try await capture(take, human: human, renderer: renderer, inputs: inputs, destination: destination)
                            try expected.write(to: marker, options: .atomic)
                        }
                        catch
                        {
                            failed.append(take.takeID)
                            print("Failed \(take.takeID): \(error)")
                        }
                    }
                    return failed
                }
            }
            var failed: [String] = []
            for await result in group { failed.append(contentsOf: result) }
            return failed
        }
        guard failed.isEmpty else { throw Failure.badSamples(failed.joined(separator: ", ")) }
        print("Rendered \(takes.count) Default Human previews.")
    }

    static func capture(
        _ take: Take,
        human: MotionCaptureHuman,
        renderer: CharacterRenderer,
        inputs: URL,
        destination: URL,
    ) async throws
    {
        let filename = "\(take.takeID).bvh"
        let data = try Data(contentsOf: inputs.appending(path: filename))
        let motion = try CMUBVHMotion(BVHMotion(data: data, fileName: filename))
        guard motion.frameCount == take.capturedFrames.count,
              let poster = take.capturedFrames.firstIndex(of: take.posterFrame)
        else { throw Failure.badSamples(take.takeID) }

        let clip = try MotionClipInput.cmuBVH(motion).retarget(human.rig, postureDegrees: human.postureDegrees)
        let headings = try clip.rootHeadings()
        let posterPlacement = CharacterJointClip.Placement(yaw: -headings[poster], offset: .zero)
        let poses = try take.capturedFrames.indices.map
        { index in
            let sample = try clip.skinningSample(at: Double(index) * clip.frameInterval, placement: posterPlacement)
            return try human.pose(palette: sample.matrices, translation: .zero, recordingSize: nil, showsSkeleton: false)
        }
        let posterPose = poses[poster]
        let posterExtent = simd_max(posterPose.framing.body.halfExtent, human.referenceBodyBounds.halfExtent)
        let animationExtent = poses.reduce(posterExtent) { simd_max($0, $1.framing.body.halfExtent) }
        try FileManager.default.createDirectory(at: destination, withIntermediateDirectories: true)

        let posterPNG = try await renderer.renderThumbnailPNG(
            frame: posterPose,
            skinColor: human.skinColor,
            skinMaterial: human.skinMaterial,
            accessoryColorOverrides: human.accessoryColorOverrides,
            size: ProjectThumbnailResolution.standard.rawValue,
            bounds: bounds(posterPose, extent: posterExtent),
            yaw: .pi - 0.55,
        )
        try posterPNG.write(to: destination.appending(path: "still.png"), options: .atomic)
        let animationSize = 256
        for (order, capturedFrame) in take.animationFrames.enumerated()
        {
            guard let index = take.capturedFrames.firstIndex(of: capturedFrame)
            else { throw Failure.badSamples(take.takeID) }
            let pose = poses[index]
            let animationPNG = try await renderer.renderThumbnailPNG(
                frame: pose,
                skinColor: human.skinColor,
                skinMaterial: human.skinMaterial,
                accessoryColorOverrides: human.accessoryColorOverrides,
                size: animationSize,
                bounds: bounds(pose, extent: animationExtent),
                yaw: .pi - 0.55,
            )
            try animationPNG.write(to: destination.appending(path: "frame-\(order).png"), options: .atomic)
        }
    }

    static func bounds(
        _ frame: CharacterPreviewFrame,
        extent: SIMD3<Float>,
    ) -> CharacterCameraBounds
    {
        let radius = max(extent.y, simd_length(SIMD2(extent.x, extent.z)))
        return CharacterCameraBounds(
            center: frame.framing.body.center - SIMD3(0, radius * 0.13, 0),
            halfExtent: extent * 1.14,
        )
    }
}
