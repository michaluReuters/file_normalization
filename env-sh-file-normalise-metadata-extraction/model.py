import os
import platform
import re
import subprocess


def slice_stream_tags(datalines: []) -> []:
    """
    Slices the input data to return a list of tuples representing the positions of each
    [STREAM]...[/STREAM] tag pair in the input.

    Args:
        datalines (list): A list of strings representing the input data.

    Returns:
        list: A list of tuples where each tuple represents the positions of the first and
        last tag in a [STREAM]...[/STREAM] tag pair in the input data.

    Raises:
        Exception: If the number of opening and closing tags do not match.

    Example:
        datalines = ["some text", "[STREAM]", "stream data", "[/STREAM]", "some more text"]
        result = slice_stream_tags(datalines)
        # result = [(1, 3)]
    """

    first_tag_positions = [i for i in range(len(datalines)) if datalines[i] == '[STREAM]']
    second_tag_positions = [i for i in range(len(datalines)) if datalines[i] == '[/STREAM]']

    if len(first_tag_positions) != len(second_tag_positions):
        raise Exception('Number of opening and closing tags do not match.')

    result = list(zip([i + 1 for i in first_tag_positions], second_tag_positions))

    return result


class FFProbe:
    """
    FFProbe wraps the ffprobe command and pulls the data into an object form::
        metadata=FFProbe('multimedia-file.mov')
    """

    def __init__(self, video_file):
        self.video_file = video_file

        # Check if ffprobe is available
        try:
            with open(os.devnull, 'w') as tempf:
                subprocess.check_call(["./ffprobe", "-h"], stdout=tempf, stderr=tempf)
        except Exception as exc:
            raise IOError(f'The ffprobe not found. Exception is: {exc}')

        if os.path.isfile(video_file):
            if str(platform.system()) == 'Windows':
                cmd = ["./ffprobe", "-show_streams ", self.video_file]
            else:
                cmd = ["./ffprobe -show_streams " + self.video_file]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            self.streams = []
            self.video = []
            self.audio = []
            datalines = []

            for a in iter(p.stdout.readline, b''):
                stream_value = re.findall(r"\s?'(.+?)\\+", str(a))
                datalines.append(stream_value[0])

            stream_slices = slice_stream_tags(datalines)

            for i in stream_slices:
                dataline_slice = datalines[i[0]:i[1]]
                for j in dataline_slice:
                    if "=" not in j:
                        dataline_slice.remove(j)
                self.streams.append(FFStream(dataline_slice))

            p.stdout.close()
            p.stderr.close()

            # Separate to each individual types base on codec_type
            for a in self.streams:
                if a.is_audio():
                    self.audio.append(a)
                if a.is_video():
                    self.video.append(a)
        else:
            raise IOError('No such media file ' + video_file)

    def show_json_format(self):
        result = []
        for i in self.streams:
            result.append(i.__dict__)
        return result


class FFStream:
    """
    An object representation of an individual stream in a multimedia file.
    """

    def __init__(self, datalines):
        for a in datalines:
            (key, val) = a.strip().split('=')
            self.__dict__[key] = val
        self.codec_type = self.__dict__["codec_type"]

    def is_audio(self):
        """
        Is this stream labelled as an audio stream?
        """
        val = False
        if self.__dict__['codec_type']:
            if str(self.__dict__['codec_type']) == 'audio':
                val = True
        return val

    def is_video(self):
        """
        Is the stream labelled as a video stream.
        """
        val = False
        if self.__dict__['codec_type']:
            if self.codec_type == 'video':
                val = True
        return val


class FFprobeDTO:
    # TODO HERE WE WILL ASK APP CONFIG FOR THE REQUIRED CONFIGURATION
    required_video_stream_variables = (
        "codec_type",
        "codec_name",
        "width",
        "height",
        "field_order",
        "r_framerate",
        "avg_frame_rate",
        "time_base",
        "pix_fmt",
        "color_range",
        "colour_space",
        "transfer",
        "primaries"
    )

    required_audio_stream_variables = (
        "codec_type",
        "codec_name",
        "sample_rate",
        "bits_per_sample",
        "channels"
    )

    def __init__(self):
        self.data = {}

    def gather_required_data(self, metadata: FFProbe, audio_data=required_audio_stream_variables,
                             video_data=required_video_stream_variables):
        count = 0
        for stream in metadata.streams:
            self.data[f"index_{count}"] = {}
            if stream.is_audio():
                for i in audio_data:
                    try:
                        if bool(stream.__dict__[i]):
                            self.data[f"index_{count}"][i] = stream.__dict__[i]
                    except Exception as exc:
                        print(f"Unable to find reference for: {exc}")
                        pass
            elif stream.is_video():
                for i in video_data:
                    try:
                        if bool(stream.__dict__[i]):
                            self.data[f"index_{count}"][i] = stream.__dict__[i]
                    except Exception as exc:
                        print(f"Unable to find reference for: {exc}")
                        pass
            count += 1
