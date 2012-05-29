"""
An s3gStreamDecoder that returns unmodified payloads from the stream
"""

import coding
import s3gStreamDecoder
import struct
import array

class s3gStreamDecoderRaw(s3gStreamDecoder.s3gStreamDecoder):

  def GetCommandFormat(self, cmd):
    """Because the Raw decoder always has information as bytes, we override the super's GetCommandFormat function with our own, that unpacks the byte value and gets the commandInfo

    @param cmd: A bytearray containing the command
    @return: The information associated with the command
    """
    hashableCmd = array.array('B', cmd)
    hashableCmd = struct.unpack('<B', hashableCmd)[0]
    return s3gStreamDecoder.commandFormats[hashableCmd]

  def ParseParameter(self, formatString, bytes):
    """Because we always want the raw data pulled out of the stream we are reading, we override the super's ParseParameter function with our own that just takes the bytes and throws them into a byte array

    @param formatString: The format we want to unpack the bytes in
    @param bytes: The bytes that were just read in
    @return The bytes that were passed in wrapped in a bytearray
    """
    returnBytes = bytearray()
    coding.AddObjToPayload(returnBytes, bytes)
    return returnBytes

  def PackagePacket(self, *args):
    """Packages all args into a single bytearray.

    @param bytearray args: A list of args, all of them bytearrays
    @return bytearray package: A collated bytearray comprised of all args
    """
    package = bytearray()
    coding.AddObjToPayload(package, args)
    return package