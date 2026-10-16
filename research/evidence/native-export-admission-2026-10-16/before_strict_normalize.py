"""Research-only consumer for the frozen Xcode RenderPreview response shapes.

A normalized snapshot path is not content acceptance or runtime provenance.
This module never opens a path supplied by a tool response.
"""
import hashlib
import io
from PIL import Image
import json
from pathlib import PurePosixPath
from sentinel_pixels import check

class Rejected(ValueError):
    pass

def normalize(result):
    if not isinstance(result,dict):
        raise Rejected('Tool result must be an object')
    flag=result.get('isError',False)
    if type(flag) is not bool or flag:
        raise Rejected('Native tool reports failure or invalid error flag')
    content=result.get('content')
    if not isinstance(content,list) or len(content)!=1:
        raise Rejected('Expected one native JSON text representation')
    block=content[0]
    if not isinstance(block,dict) or block.get('type')!='text':
        raise Rejected('Expected native text block')
    text=block.get('text')
    if not isinstance(text,str) or len(text.encode('utf-8'))>65536:
        raise Rejected('Native text representation missing or exceeds bound')
    try:
        payload=json.loads(text)
    except (ValueError,RecursionError) as error:
        raise Rejected('Invalid native JSON') from error
    if not isinstance(payload,dict):
        raise Rejected('Native payload must be an object')
    if 'structuredContent' in result and result['structuredContent']!=payload:
        raise Rejected('Conflicting native representations')
    allowed={'errors','previewSnapshotPath','supportedLocalizations','supportedPreviewVariantOverrides'}
    if set(payload)-allowed or payload.get('errors')!=[]:
        raise Rejected('Native error, unknown payload shape or missing error list')
    path=payload.get('previewSnapshotPath')
    if not isinstance(path,str) or not path.startswith('/') or len(path)>4096 or '\x00' in path or str(PurePosixPath(path))!=path or '..' in PurePosixPath(path).parts:
        raise Rejected('Snapshot path must be canonical and absolute')
    return {'snapshot_path':path,'grade':'response-shape-only','content_accepted':False}

def admit_frozen_sentinel(result, png_bytes, expected):
    """Expected mapping comes from the separately sealed owned fixture record."""
    normalized=normalize(result)
    if normalized['snapshot_path']!=expected['native_path']:
        raise Rejected('Frozen request/image path binding mismatch')
    if hashlib.sha256(png_bytes).hexdigest()!=expected['png_sha256']:
        raise Rejected('Frozen PNG identity mismatch')
    if len(png_bytes)>1048576:
        raise Rejected('PNG byte budget exceeded')
    try:
        with Image.open(io.BytesIO(png_bytes)) as image:
            if image.format!='PNG' or image.size!=(320,200):
                raise Rejected('PNG format or dimensions differ from sentinel')
            rgba=image.convert('RGBA').tobytes();size=image.size
    except OSError as error:
        raise Rejected('PNG decode failed') from error
    if not check(rgba,size,expected['mode']):
        raise Rejected('Owned sentinel pixel expectations failed')
    return {'grade':'frozen-owned-sentinel-color-content','content_accepted':True,
            'live_provenance':False,'glyph_raster_verified':False}
