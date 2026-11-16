"""Full SHA-256 hashes of the 584 cube formulas, for both line-ending conventions.

usage: python3 hash_manifest.py OUT.tsv

Writes one line per canonical cube:  index  cube  sha256(CRLF file)  sha256(LF file).
The CRLF hash is what gen_cnf.py produces on Windows (where the certificates were made),
the LF hash what it produces on Linux. No CNF files are written.
"""
import sys, hashlib
from gen_cnf import canon, cubes, cube_parts, base_body

nv, ncl, hb, body = base_body()
body_lf = body.encode()
body_crlf = body.replace('\n', '\r\n').encode()
with open(sys.argv[1], 'w', newline='\n') as out:
    out.write('cube\tsixtuple\tsha256_crlf\tsha256_lf\n')
    for ci in canon:
        head, _, tail = cube_parts(ci)
        hl = hashlib.sha256(); hc = hashlib.sha256()
        for part_lf, part_crlf in ((head.encode(), head.replace('\n', '\r\n').encode()),
                                   (body_lf, body_crlf),
                                   (tail.encode(), tail.replace('\n', '\r\n').encode())):
            hl.update(part_lf); hc.update(part_crlf)
        out.write(f'{ci}\t{"".join(map(str, cubes[ci]))}\t{hc.hexdigest()}\t{hl.hexdigest()}\n')
print('wrote', len(canon), 'hashes to', sys.argv[1])
