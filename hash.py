import hashlib

#
# Calculate the hash value of a file
#
def hashfile(afile, hasher, blocksize=65536):
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    return hasher.hexdigest()

#
# Check whether a file match a given MD5 value
#
def md5match(afile, md5sumvalue):
    if not md5sumvalue:
        return True
    else:
        return hashfile(open(afile, 'rb'), hashlib.md5()) == md5sumvalue

