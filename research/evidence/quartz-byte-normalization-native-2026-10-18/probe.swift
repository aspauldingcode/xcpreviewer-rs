// Prospective owned public Quartz byte-domain control. Not executed in this wake.
import AppKit
import CryptoKit
import Darwin

@main struct ByteNormalization {
    static func main() throws {
        alarm(10)
        FileHandle.standardError.write(Data("owned_tree_pid:\(getpid())\n".utf8))
        func emit(_ value:[String:Any]) throws {
            var data=try JSONSerialization.data(withJSONObject:value,options:[.sortedKeys])
            data.append(10);FileHandle.standardOutput.write(data)
        }
        let args=CommandLine.arguments
        if args.count==3 && args[1]=="--output-control" && args[2]=="output-valid" {
            try emit(["pid":getpid(),"status":"owned_output_control"]);return
        }
        guard args.count==3 && args[1]=="--fixture",
              let space=CGColorSpace(name:CGColorSpace.linearSRGB) else {
            throw NSError(domain:"ByteNormalization",code:1)
        }
        let width=256,height=3,sourceStride=1040,destStride=4112,allocation=16384
        // Each byte appears in every RGB component; channel permutations prevent a
        // grayscale-only fast path. Opaque alpha isolates normalization.
        var source=[UInt8](repeating:0x5a,count:sourceStride*height)
        for y in 0..<height {for x in 0..<width {
            let offset=y*sourceStride+x*4
            source[offset]=UInt8(x);source[offset+1]=UInt8((x+85*y+37)%256)
            source[offset+2]=UInt8((255-x+17*y)%256);source[offset+3]=255
        }}
        let sourceData=Data(source)
        guard let provider=CGDataProvider(data:sourceData as CFData),
              let image=CGImage(width:width,height:height,bitsPerComponent:8,bitsPerPixel:32,
                               bytesPerRow:sourceStride,space:space,
                               bitmapInfo:CGBitmapInfo(rawValue:CGImageAlphaInfo.premultipliedLast.rawValue),
                               provider:provider,decode:nil,shouldInterpolate:false,intent:.defaultIntent) else {
            throw NSError(domain:"ByteNormalization",code:2)
        }
        try sourceData.write(to:URL(fileURLWithPath:args[2]).appendingPathComponent("source.raw"))
        // A/A repeat within one process. Destination padding and tail are sentinels.
        for phase in 0..<2 {
            var bytes=[UInt8](repeating:0xa5,count:allocation)
            for y in 0..<height {for x in 0..<(width*16) {bytes[y*destStride+x]=0}}
            try bytes.withUnsafeMutableBytes { buffer in
                let info=CGBitmapInfo.floatComponents.rawValue|CGBitmapInfo.byteOrder32Little.rawValue|CGImageAlphaInfo.premultipliedLast.rawValue
                guard let context=CGContext(data:buffer.baseAddress,width:width,height:height,bitsPerComponent:32,bytesPerRow:destStride,space:space,bitmapInfo:info) else {
                    throw NSError(domain:"ByteNormalization",code:3)
                }
                context.setBlendMode(.copy);context.interpolationQuality = .none
                context.draw(image,in:CGRect(x:0,y:0,width:width,height:height))
                let data=Data(buffer),name="phase\(phase).raw"
                try data.write(to:URL(fileURLWithPath:args[2]).appendingPathComponent(name))
                try emit(["pid":getpid(),"phase":phase,"file":name,"width":width,"height":height,"stride":destStride,"allocation_bytes":allocation,"sha256":SHA256.hash(data:data).map{String(format:"%02x",$0)}.joined(),"color_space":context.colorSpace?.name as String? ?? "unnamed","bitmap_info":context.bitmapInfo.rawValue,"source_sha256":SHA256.hash(data:sourceData).map{String(format:"%02x",$0)}.joined()])
            }
        }
    }
}
