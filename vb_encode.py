import argparse
import math
import multiprocessing
from natsort import os_sorted
import os
from PIL import Image
from reedsolo import RSCodec, ReedSolomonError
import shutil
import subprocess
import time
import vb_common


ENC_VERSION_NUM = 2
BLOCK_SIZE = 128
# not the prettiest implementation but hey, it works
COLOR_PALETTES = {
    "256": [(0, 0, 0), (0, 0, 85), (36, 0, 85), (0, 182, 85), (73, 0, 85), (109, 0, 85), (73, 182, 170), (182, 182, 255), (255, 255, 0), (0, 0, 170), (182, 0, 85), (146, 182, 170), (219, 0, 85), (109, 109, 0), (182, 146, 255), (255, 0, 85), (0, 73, 255), (109, 219, 170), (36, 0, 0), (182, 73, 170), (0, 255, 170), (73, 73, 170), (219, 109, 170), (36, 109, 255), (255, 109, 85), (0, 146, 255), (182, 219, 170), (109, 255, 85), (182, 73, 85), (219, 219, 85), (255, 219, 170), (0, 36, 255), (146, 219, 255), (255, 109, 0), (0, 146, 170), (219, 255, 0), (255, 255, 85), (0, 0, 255), (36, 36, 85), (182, 0, 255), (219, 219, 255), (73, 0, 0), (73, 146, 0), (109, 146, 0), (73, 36, 170), (146, 146, 0), (182, 36, 85), (73, 146, 85), (146, 219, 170), (36, 219, 170), (255, 0, 170), (219, 36, 170), (255, 182, 85), (182, 219, 85), (0, 255, 255), (73, 109, 0), (182, 109, 255), (36, 255, 170), (109, 0, 0), (255, 219, 85), (0, 36, 170), (73, 255, 170), (146, 255, 0), (109, 109, 255), (109, 255, 170), (109, 146, 170), (182, 255, 0), (255, 219, 0), (0, 36, 85), (219, 255, 85), (255, 109, 170), (73, 0, 255), (73, 146, 170), (109, 146, 85), (255, 146, 85), (0, 109, 85), (146, 0, 0), (146, 36, 0), (182, 36, 0), (146, 146, 255), (219, 0, 170), (255, 36, 0), (0, 73, 170), (146, 36, 85), (0, 219, 170), (73, 73, 255), (109, 73, 170), (255, 73, 255), (0, 182, 0), (146, 109, 85), (255, 255, 170), (182, 0, 0), (73, 182, 85), (219, 109, 85), (182, 219, 255), (36, 182, 85), (146, 182, 85), (73, 36, 85), (255, 109, 255), (73, 182, 0), (36, 146, 170), (146, 0, 255), (0, 255, 0), (146, 182, 0), (146, 36, 170), (182, 0, 170), (219, 36, 85), (73, 255, 0), (219, 0, 0), (219, 182, 0), (36, 255, 255), (255, 182, 0), (0, 73, 85), (73, 255, 255), (255, 146, 170), (0, 109, 255), (109, 255, 255), (73, 73, 85), (219, 182, 85), (182, 255, 85), (146, 73, 85), (219, 255, 170), (182, 219, 0), (146, 109, 255), (73, 36, 0), (146, 219, 0), (219, 73, 85), (73, 146, 255), (255, 0, 0), (0, 73, 0), (146, 0, 170), (109, 219, 255), (36, 146, 0), (182, 182, 85), (0, 182, 170), (255, 219, 255), (109, 36, 85), (36, 36, 255), (36, 146, 255), (146, 146, 170), (73, 182, 255), (146, 0, 85), (20, 219, 85), (219, 146, 170), (73, 109, 85), (219, 36, 0), (182, 36, 255), (219, 182, 170), (255, 146, 0), (0, 109, 0), (146, 73, 255), (36, 73, 0), (36, 73, 85), (146, 182, 255), (109, 73, 85), (73, 255, 85), (36, 219, 255), (146, 109, 0), (36, 73, 170), (146, 255, 255), (219, 73, 170), (255, 73, 85), (0, 146, 85), (146, 146, 85), (36, 0, 255), (146, 36, 255), (0, 182, 255), (73, 73, 0), (219, 146, 85), (109, 0, 170), (255, 36, 170), (73, 36, 255), (182, 146, 0), (109, 182, 85), (73, 219, 85), (219, 146, 0), (0, 109, 170), (36, 109, 0), (219, 36, 255), (109, 182, 170), (255, 182, 170), (36, 73, 255), (73, 219, 0), (219, 219, 0), (146, 219, 85), (109, 73, 0), (73, 109, 255), (109, 109, 170), (219, 219, 170), (255, 182, 255), (219, 109, 0), (109, 219, 0), (0, 36, 0), (36, 36, 0), (255, 255, 255), (73, 0, 170), (219, 0, 255), (36, 182, 170), (109, 36, 0), (219, 182, 255), (146, 73, 0), (109, 36, 170), (109, 182, 255), (182, 182, 0), (255, 0, 255), (0, 255, 85), (182, 182, 170), (36, 255, 85), (146, 109, 170), (109, 36, 255), (255, 36, 255), (0, 219, 255), (109, 255, 0), (219, 73, 255), (109, 73, 255), (146, 255, 170), (73, 219, 170), (109, 219, 85), (146, 73, 170), (36, 36, 170), (182, 73, 0), (182, 109, 0), (36, 219, 0), (255, 73, 170), (0, 146, 0), (182, 255, 255), (36, 0, 170), (219, 255, 255), (182, 109, 85), (36, 146, 85), (109, 0, 255), (182, 255, 170), (109, 146, 255), (36, 255, 0), (182, 36, 170), (219, 73, 0), (182, 146, 85), (255, 36, 85), (0, 219, 0), (146, 255, 85), (219, 146, 255), (73, 109, 170), (109, 109, 85), (36, 109, 85), (36, 219, 85), (182, 146, 170), (73, 219, 255), (182, 73, 255), (36, 182, 0), (255, 146, 255), (219, 109, 255), (182, 109, 170), (36, 109, 170), (109, 182, 0), (36, 182, 255), (255, 73, 0)],
    "16": [(0, 0, 0), (17, 21, 178), (33, 181, 50), (40, 182, 183), (192, 27, 25), (190, 38, 179), (190, 106, 37), (184, 184, 184), (104, 104, 104), (99, 109, 247), (76, 251, 122), (70, 253, 253), (251, 111, 109), (252, 116, 249), (254, 253, 127), (255, 255, 255)],
    "4": [(0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255)],
    #"2": [(0, 0, 0), (255, 255, 255)]
    "2": [0, 255]
}


def concat_files(files, output: str):
    with open(output, "wb") as output_file:
        for f in files:
            with open(f, "rb") as input_file:
                output_file.write(input_file.read())


def build_frame(data: bytearray, width: int, height: int, count: int, pixel_size: int, palette_size: int, fps: int, video_codec: str):
    """Encodes a byte array into an image"""
    internal_width = int(width / pixel_size)
    internal_height = int(height / pixel_size)
    if len(data) > (internal_width * internal_height) / math.log(256, palette_size):
        raise ValueError("Bytearray is too large for the image size!")
    if palette_size == 2:
        image = Image.new("L", (internal_width, internal_height))
    else:
        image = Image.new("RGB", (internal_width, internal_height))
    color_palette = COLOR_PALETTES[str(palette_size)]
    for (num, byte) in enumerate(data):
        # TODO: improve the 16 and 4 color palette branches once i figure out the maths behind it
        if palette_size == 256:
            image.putpixel(((num % internal_width), math.floor(num / internal_width)), color_palette[byte])
        elif palette_size == 16:
            first_pixel = (((num * 2) % internal_width), math.floor((num * 2) / internal_width))
            second_pixel = ((((num * 2) + 1) % internal_width), math.floor(((num * 2) + 1) / internal_width))
            first_part = (byte & 0b11110000) >> 4
            second_part = byte & 0b00001111
            image.putpixel(first_pixel, color_palette[first_part])
            image.putpixel(second_pixel, color_palette[second_part])
        elif palette_size == 4:
            first_pixel = (((num * 4) % internal_width), math.floor((num * 4) / internal_width))
            second_pixel = ((((num * 4) + 1) % internal_width), math.floor(((num * 4) + 1) / internal_width))
            third_pixel = ((((num * 4) + 2) % internal_width), math.floor(((num * 4) + 2) / internal_width))
            fourth_pixel = ((((num * 4) + 3) % internal_width), math.floor(((num * 4) + 3) / internal_width))
            first_part = (byte & 0b11000000) >> 6
            second_part = (byte & 0b00110000) >> 4
            third_part = (byte & 0b00001100) >> 2
            fourth_part = byte & 0b00000011
            image.putpixel(first_pixel, color_palette[first_part])
            image.putpixel(second_pixel, color_palette[second_part])
            image.putpixel(third_pixel, color_palette[third_part])
            image.putpixel(fourth_pixel, color_palette[fourth_part])
        elif palette_size == 2:
            for i in range(0, 8):
                pixel = ((((num * 8) + i) % internal_width), math.floor(((num * 8) + i) / internal_width))
                # this god forsaken line gets the i'th bit
                part = (byte & (int(128 / (2**i)))) >> (7-i)
                image.putpixel(pixel, color_palette[part])
    image = image.resize((width, height), resample=Image.NEAREST)
    image.save(os.path.join("tmp", "%d.png" % count))
    subprocess.run(["ffmpeg", "-y", "-r", str(fps), "-i", os.path.join("tmp", "%d.png" % count), "-t", str(1/fps), "-c:v", video_codec, "-bsf:v", "h264_mp4toannexb", "-f", "mpegts", os.path.join("tmp", "%d.ts" % count)],
                   stdout=subprocess.PIPE,
                   stderr=subprocess.STDOUT)
    os.remove(os.path.join("tmp", "%d.png" % count))
    return os.path.join("tmp", "%d.ts" % count)


def build_frames(input_file: str, width: int, height: int, pixel_size: int, palette_size: int, threads: int, ecc_bytes: int, video_codec: str, fps: int, output_file: str):
    """Encodes any file into images."""
    # first frame will always be metadata
    file = open(input_file, "rb")
    filesize = os.path.getsize(input_file)
    if len(file.name) > 512:
        raise ValueError("File names longer than 512 characters are not supported!")
    # future-proofing for the next century, file sizes larger than that cannot be written down in the metadata frame
    if filesize > (256 ** 8) - 1:
        raise ValueError("Files bigger than %d bytes are not supported!" % ((256 ** 8) - 1))
    blocks_per_frame = math.floor((width * height) / (pixel_size ** 2) / int(math.log(256, palette_size)) / BLOCK_SIZE)
    content_bytes_per_block = BLOCK_SIZE - ecc_bytes
    content_bytes_per_frame = blocks_per_frame * content_bytes_per_block
    needed_frames = int(math.ceil(filesize / content_bytes_per_frame)) + 1
    print("Needed amount of frames are %d." % (needed_frames))
    print("Video length is %d seconds." % (needed_frames / args.fps))
    
    # metadata looks like this: bytes 0 and 1 are the encoding version, bytes 2-4 are for the palette size, byte 5 is the pixel size, bytes 6-13 is the file size, bytes 14-33 are the SHA1 checksum, byte 34 is the amount of ECC bytes, bytes 35-546 are the filename
    # the metadata frame always has 32 bytes of ECC, regardless of whether strong_ecc is True or False
    meta_bytes = bytearray()
    meta_ecc = RSCodec(32)
    meta_bytes += ENC_VERSION_NUM.to_bytes(2, byteorder="big")
    meta_bytes += palette_size.to_bytes(2, byteorder="big")
    meta_bytes += pixel_size.to_bytes(1, byteorder="big")
    meta_bytes += os.path.getsize(input_file).to_bytes(8, byteorder="big")
    meta_bytes += vb_common.sha1_file(input_file)
    meta_bytes += ecc_bytes.to_bytes(1, byteorder="big")
    meta_bytes += os.path.basename(file.name + (((512 - len(file.name)) * '\0'))).encode("utf-8") # fill the file name with nulls so we have fixed length metadata
    # the metadata frame is our first partial video, we use MPEG-2 TS as a container since concatenating with it requires little effort
    os.rename(build_frame(meta_ecc.encode(meta_bytes), width, height, 0, pixel_size, palette_size, fps, video_codec), os.path.join("tmp", "partial.ts"))
    print(f"Built metadata frame; 1/{needed_frames} ({(1/needed_frames):.2f} %).")
    ecc = RSCodec(ecc_bytes)
    
    # rather unoptimized multithreading, to be improved
    def work(num: int):
        # seek to the correct position as with multithreading this seems to fail quite a lot
        bytearray_to_encode = bytearray()
        file.seek((num - 1) * content_bytes_per_frame)
        all_bytes = file.read(content_bytes_per_frame)
        cur_bytes = bytearray()
        for i in range(0, blocks_per_frame):
            try:
                cur_bytes = all_bytes[(i * content_bytes_per_block):((i + 1) * content_bytes_per_block)]
            # if we reached the end of the file, we might have not read 256 bytes, append NULLs in this case
            except:
                cur_bytes = all_bytes[(i * content_bytes_per_block):]
                for i in range(0, len(cur_bytes) - content_bytes_per_block):
                    cur_bytes.append(0x00)
            bytearray_to_encode += ecc.encode(cur_bytes)
        build_frame(bytearray_to_encode, width, height, num, pixel_size, palette_size, fps, video_codec)
    cur_frame = 1
    
    while cur_frame < needed_frames:
        jobs = []
        frames = []
        for i in range(threads):
            # we need to check again because the loop might terminate too late
            if(cur_frame < needed_frames):
                frames.append("%d.ts" % cur_frame)
                p = multiprocessing.Process(target=work, args=(cur_frame,))
                cur_frame += 1
                jobs.append(p)
                p.start()
                # wait until the process actually started
                time.sleep(0.05)
        for job in jobs:
            job.join()
        frames = os_sorted(frames)
        frames.insert(0, "partial.ts")
        with open(os.path.join("tmp", "list.txt"), "w") as l:
            for f in frames:
                l.write("file '" + f + "'\n")
        #concat_files(frames, os.path.join("tmp", "new_partial.ts"))
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-r", str(fps), "-i", os.path.join("tmp", "list.txt"), "-c", "copy", os.path.join("tmp", "new_partial.ts")],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT)
        for f in frames:
            os.remove(os.path.join("tmp", f))
        os.remove(os.path.join("tmp", "list.txt"))
        os.rename(os.path.join("tmp", "new_partial.ts"), os.path.join("tmp", "partial.ts"))
        percent = ((cur_frame)/needed_frames)*100
        print(f"Built all frames up to {cur_frame}/{needed_frames} ({percent:.2f} %).")
    print(f"Converting into desired format...")
    subprocess.run(["ffmpeg", "-y", "-r", str(fps), "-i", os.path.join("tmp", "partial.ts"), "-c", "copy", output_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT)
    file.close()


if __name__ == "__main__":
    start_time = time.time()
    
    parser = argparse.ArgumentParser(description="Tool to turn raw data into videos.")
    parser.add_argument("input", metavar="input_file", type=str, help="The file to be turned into a video file.")
    parser.add_argument("output", metavar="output_file", type=str, help="The location of the resulting video file.")
    parser.add_argument("--fps", metavar="fps", type=float, help="FPS of the video, keep it very low (between 0.25-6) to avoid compression artifacts. Use 6 if you want to upload the file to YouTube.", default=1.0)
    parser.add_argument("--width", metavar="width", type=int, help="Width of the video.", default=3840)
    parser.add_argument("--height", metavar="height", type=int, help="Height of the video.", default=2160)
    parser.add_argument("--video_codec", metavar="video_codec", type=str, help="Tells ffmpeg which video encoder to use.", default="libx264")
    parser.add_argument("--crf", metavar="crf", type=int, help="Quality of the video (constant rate factor). *Lower* values will increase quality (therefore less compression artifacts) and file size. Might not work with every video codec.", default=24)
    parser.add_argument("--pixel_size", metavar="pixel_size", type=int, help="The size each pixel is supposed to be. Larger sizes will create much larger video files but might be more resilient against compression.", default=1)
    parser.add_argument("--color_palette", metavar="color_palette", type=int, help="The color palette size to use. The smaller the size, less colors make the video more resilient against compression but also make the video bigger and encoding/decoding slower.", default=2)
    parser.add_argument("--ecc_bytes",metavar="ecc_bytes", type=int, help="Determines the amount of Error Correction Code (ECC) bytes that will be used in a 128 bytes segment. More bytes = slightly bigger file size, slightly longer en/decoding time, more resilience against compression.", default=12)
    parser.add_argument("--threads", metavar="threads", type=int, help="Amount of threads to use for encoding. Defaults to all available cores.", default=len(os.sched_getaffinity(0)))

    print("IMPORTANT: THIS TOOL COMES WITH NO WARRANTY WHATSOEVER. USE AT YOUR OWN RISK.")
    
    args = parser.parse_args()
    
    if args.width * args.height < 1024:
        raise ValueError("The video must have atleast 1024 pixels per frame!")
    
    if args.threads < 1:
        raise ValueError("Threads must be atleast 1!")
    
    if args.ecc_bytes < 1:
        raise ValueError("There must be atleast 1 ECC byte per 128 bytes!")
    
    if args.ecc_bytes > 127:
        raise ValueError("There cannot be more than 127 ECC bytes per 128 bytes!")
    
    if args.ecc_bytes > 64:
        print("More than 64 bytes ECC barely bring any benefit, consider lowering it to reduce en/decoding time and file size.")
    
    if str(args.color_palette) not in COLOR_PALETTES.keys():
        raise ValueError("Invalid color palette size! Use one of these values: %s." % str(list(COLOR_PALETTES.keys())))
    
    print("Starting encoding process.")
    print("\"Bandwidth\" of the video will be approx. %dB/s." % math.floor((args.width * args.height * args.fps) / math.log(256, args.color_palette) / (args.pixel_size ** 2) / (BLOCK_SIZE / (BLOCK_SIZE - args.ecc_bytes))))
    
    if not os.path.exists("tmp"):
    	os.mkdir("tmp")
    
    frames = build_frames(args.input, args.width, args.height, args.pixel_size, args.color_palette, args.threads, args.ecc_bytes, args.video_codec, args.fps, args.output)
    #start_ffmpeg(list_file, args.video_codec, args.fps, args.crf, args.output)
    print("Done! Cleaning up.")
    shutil.rmtree("tmp")
    
    print("Process took %.2f seconds." % (time.time() - start_time))
