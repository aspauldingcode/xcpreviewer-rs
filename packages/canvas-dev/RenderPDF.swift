import Foundation
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers
@main struct RenderPDF {
 static func main() throws {
  let a=CommandLine.arguments
  guard a.count==5,let width=Int(a[2]),let height=Int(a[3]),width>0,height>0,width*height<=8_388_608,
        let pdf=CGPDFDocument(URL(fileURLWithPath:a[1]) as CFURL),let page=pdf.page(at:1),
        let space=CGColorSpace(name:CGColorSpace.sRGB),
        let context=CGContext(data:nil,width:width,height:height,bitsPerComponent:8,bytesPerRow:width*4,space:space,bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue) else {throw Failure.invalid}
  let box=page.getBoxRect(.mediaBox)
  context.scaleBy(x:CGFloat(width)/box.width,y:CGFloat(height)/box.height)
  context.translateBy(x:-box.minX,y:-box.minY);context.drawPDFPage(page)
  guard let image=context.makeImage(),let destination=CGImageDestinationCreateWithURL(URL(fileURLWithPath:a[4]) as CFURL,UTType.png.identifier as CFString,1,nil) else {throw Failure.invalid}
  CGImageDestinationAddImage(destination,image,nil)
  guard CGImageDestinationFinalize(destination) else {throw Failure.invalid}
  print("{\"pdf_width\":\(box.width),\"pdf_height\":\(box.height),\"width\":\(width),\"height\":\(height)}")
 }
 enum Failure:Error{case invalid}
}
