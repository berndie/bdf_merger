"""Script to merge multiple BDF files using only the standard library."""
import abc
import argparse
import datetime
import multiprocessing
import os
import time
import logging
import sys
from pathlib import Path
from typing import (
    IO,
    Any,
    Union,
    Tuple,
    List,
    Type,
    Sequence,
    Iterable,
    Callable,
)
from typing_extensions import Literal


class ParserABC(abc.ABC):
    """Interface for parsers."""

    @abc.abstractmethod
    def from_bytes(self, value: bytes) -> Any:
        """Parse a bytes value directly from the BDF file.

        Parameters
        ----------
        value : bytes
            A bytestring

        Returns
        -------
        Any
            Parsed value from the BDF
        """
        pass

    @abc.abstractmethod
    def to_bytes(self, value: Any, length: int) -> bytes:
        """Convert a value into bytes for the BDF file.

        Parameters
        ----------
        value : Any
            Value to convert to the bytestring
        length : int
            Required length of the bytestring. This parameter can be used to
            do padding

        Returns
        -------
        bytes
            The value, converted to bytes
        """
        pass


class BytesParser(ParserABC):
    """Parser to load bytes from/prepare bytes for a BDF file."""

    def __init__(self, padding_byte: bytes = b" "):
        """Create a BytesParser.

        Parameters
        ----------
        padding_byte : bytes
            Bytes to pad the remaining length in the header. In bdf, this is
            typically b" "

        """
        self.padding_byte = padding_byte

    def from_bytes(self, value: bytes) -> bytes:  # noqa: D102
        return value.replace(self.padding_byte, b"")

    def _to_bytes(self, value: Any):
        """Convert a value to bytes.

        Parameters
        ----------
        value : Any
            Value to convert to bytes

        Returns
        -------
        bytes
            Converted value
        """
        return value

    def to_bytes(self, value: bytes, length: int) -> bytes:  # noqa: D102
        return self.pad_bytes(self._to_bytes(value), length)

    def pad_bytes(self, value: bytes, length: int):
        """Pad a bytes value to a certain length using self.padding_byte.

        Parameters
        ----------
        value : bytes
            Bytestring to pad
        length : int
            Total required length. Padding will be added at the end of the
            bytestring to gain this total length.

        Returns
        -------
        bytes
            Padded bytes

        Raises
        ------
        ValueError
            If the length of value exceeds the specified length
        """
        if len(value) > length:
            raise ValueError(
                "The length of the raw value {} is longer than the requested "
                "length ({} > {})".format(value, len(value), length)
            )
        return value + (self.padding_byte * (length - len(value)))


class StringParser(BytesParser):
    """Parser for string values."""

    def __init__(
        self,
        *args,
        from_encoding: str = "ascii",
        to_encoding: str = "ascii",
        **kwargs
    ):
        """Create a parser for strings.

        Parameters
        ----------
        args : tuple
            Arguments for superclass
        from_encoding : str
            Encoding to convert bytes to string. See str.decode for options.
        to_encoding : str
            Decoding to convert a string to bytes. See str.decode for options.
        kwargs : dict
            Keyword arguments for superclass
        """
        super().__init__(*args, **kwargs)
        self.from_encoding = from_encoding
        self.to_encoding = to_encoding

    def from_bytes(self, value: bytes) -> str:  # noqa: D102
        return (
            super(StringParser, self)
            .from_bytes(value)
            .decode(self.from_encoding)
        )

    def _to_bytes(self, value: str) -> bytes:  # noqa: D102
        return bytes(value, self.to_encoding)


class TimeParser(StringParser):
    """Parser for time.time values."""

    def __init__(
        self,
        *args,
        from_format: str = "%H.%M.%S",
        to_format: str = "%H.%M.%S",
        **kwargs
    ):
        """Create a TimeParser.

        Parameters
        ----------
        args : tuple
            Arguments for the superclass
        from_format : str
            String format to convert bytes to a time.time
        to_format : str
            String format to convert time.time to bytes. This string will then
             be converted to bytes.
        kwargs : dict
            Keyword arguments for the superclass
        """
        super().__init__(*args, **kwargs)
        self.from_format = from_format
        self.to_format = to_format

    def from_bytes(self, value: bytes) -> time.time:  # noqa: D102
        return time.strptime(
            super(TimeParser, self).from_bytes(value), self.from_format
        )

    def _to_bytes(self, value: time.time) -> bytes:  # noqa: D102
        return super()._to_bytes(time.strftime(self.to_format, value))


class DateParser(StringParser):
    """Parser for datetime.date objects."""

    def __init__(
        self,
        *args,
        from_format: str = "%d.%m.%y",
        to_format: str = "%d.%m.%y",
        **kwargs
    ):
        """Create a date parser.

        Parameters
        ----------
        args : tuple
            Arguments for the superclass
        from_format : str
            String format to convert bytes to a datetime.date object
        to_format : str
            String format to convert datetime.time to bytes. This string will
            then be converted to bytes.
        kwargs : dict
            Keyword arguments for the superclass
        """
        super().__init__(*args, **kwargs)
        self.from_format = from_format
        self.to_format = to_format

    def from_bytes(self, value: bytes) -> datetime.date:  # noqa: D102
        return datetime.datetime.strptime(
            super().from_bytes(value), self.from_format
        ).date()

    def _to_bytes(self, value: datetime.date) -> bytes:  # noqa: D102
        return super()._to_bytes(value.strftime(self.to_format))


class IntParser(StringParser):
    """Parser for integer values."""

    def from_bytes(self, value: bytes) -> int:  # noqa: D102
        return int(value)

    def _to_bytes(self, value: int) -> bytes:  # noqa: D102
        return super(IntParser, self)._to_bytes(str(value))


class BDFHeader:
    """Header of a BDF file."""

    # Mapping derived from https://www.biosemi.com/faq/file_format.htm
    # The keys of this dictionary can be accessed on the BDFHeader object
    # itself. The values of this dictionary are dictionaries with 2 keys:
    # "boundaries" and "parser".
    #
    # boundaries:
    # The value mapped to "boundaries" defines the
    # location of the attribute in the raw binary data. In its simplest form,
    # this value contains just two integer index values. The first boundary
    # value can also be replaced with a tuple
    # (offset:int, attribute:str, multiplier:int): this will be calculated
    # to be offset + getattr(self, attribute) * multiplier.
    # The second boundary value can also be a tuple
    # (attribute:str, width:int).
    # In that case, n values will be extracted
    # (with n = range(getattr(self, attribute)), each with width 'width',
    # relative to the starting boundary.
    #
    # parser:
    # A ParserABC object that will be used to parse the extracted bytes and
    # to replace them.

    MAPPING = {
        "identification_code": {"boundaries": (0, 8), "parser": BytesParser()},
        "subject_identification": {
            "boundaries": (8, 88),
            "parser": StringParser(),
        },
        "local_recording_identification": {
            "boundaries": (88, 168),
            "parser": StringParser(),
        },
        "start_date": {"boundaries": (168, 176), "parser": DateParser()},
        "start_time": {"boundaries": (176, 184), "parser": TimeParser()},
        "bytes_in_header": {"boundaries": (184, 192), "parser": IntParser()},
        "data_format_version": {
            "boundaries": (192, 236),
            "parser": StringParser(),
        },
        "nb_data_records": {"boundaries": (236, 244), "parser": IntParser()},
        "data_duration": {"boundaries": (244, 252), "parser": IntParser()},
        "nb_channels": {"boundaries": (252, 256), "parser": IntParser()},
        "channel_labels": {
            "boundaries": (256, ("nb_channels", 16)),
            "parser": StringParser(),
        },
        "transducer_types": {
            "boundaries": ((256, "nb_channels", 16), ("nb_channels", 80)),
            "parser": StringParser(),
        },
        "dimensions": {
            "boundaries": ((256, "nb_channels", 96), ("nb_channels", 8)),
            "parser": StringParser(),
        },
        "min_dimensions": {
            "boundaries": ((256, "nb_channels", 104), ("nb_channels", 8)),
            "parser": IntParser(),
        },
        "max_dimensions": {
            "boundaries": ((256, "nb_channels", 112), ("nb_channels", 8)),
            "parser": IntParser(),
        },
        "min_digital": {
            "boundaries": ((256, "nb_channels", 120), ("nb_channels", 8)),
            "parser": IntParser(),
        },
        "max_digital": {
            "boundaries": ((256, "nb_channels", 128), ("nb_channels", 8)),
            "parser": IntParser(),
        },
        "prefiltering": {
            "boundaries": ((256, "nb_channels", 136), ("nb_channels", 80)),
            "parser": StringParser(),
        },
        "samples_per_record": {
            "boundaries": ((256, "nb_channels", 216), ("nb_channels", 8)),
            "parser": IntParser(),
        },
        "reserved": {
            "boundaries": ((256, "nb_channels", 224), ("nb_channels", 32)),
            "parser": StringParser(),
        },
    }

    # This should correspond to a key in BDFHeader.MAPPING.
    # The corresponding dictionary in BDFHeader.MAPPING should have a boundary
    # with 2 number (i.e. boundary parsing will not be possible)
    bytes_in_header_attribute = "bytes_in_header"

    # These attributes should be equal to allow for concatenation
    must_equal_for_concatenate_attributes = (
        "channel_labels",
        "samples_per_record",
        "dimensions",
    )

    # These actions will be applied when concatenating 2 BDFHeaders
    concatenate_actions = (
        {
            "attributes": ("nb_data_records", "data_duration"),
            "action": lambda x, y: x + y,
        },
        {"attributes": ("max_dimensions", "max_digital"), "action": max},
        {"attributes": ("min_dimensions", "min_digital"), "action": min},
    )

    def __init__(self, data: bytes):
        """Extract a BDF header from a BDF file.

        Parameters
        ----------
        data : bytes
            Binary data of the BDFHeader
        """
        self.data = data

    @classmethod
    def from_fp(cls, fp: IO) -> "BDFHeader":
        """Load the full header.

        Parameters
        ----------
        fp : IO
            Filepointer of the BDF file to load the header from.

        Returns
        -------
        BDFHeader
            The BDFHeader
        """
        # Go to the start
        fp.seek(0)
        header_data = b""
        # We first have to read to just after the header length field.
        # This field can then be parsed to retrieve the full length of the
        # header in bytes. Finally, that value can be used to load the full
        # header.
        bounds = cls.MAPPING[cls.bytes_in_header_attribute]["boundaries"]
        header_data += fp.read(bounds[1])
        nb_bytes = cls.MAPPING[cls.bytes_in_header_attribute][
            "parser"
        ].from_bytes(
            # fmt:off
            header_data[bounds[0]:bounds[1]]
            # fmt:on
        )
        header_data += fp.read(nb_bytes - bounds[1])
        return BDFHeader(header_data)

    @classmethod
    def from_path(
        cls, path: Union[str, Path], open_mode: str = "rb"
    ) -> "BDFHeader":
        """Create a BDFHeader from a path.

        Parameters
        ----------
        path : Union[str, Path]
            Path to load the BDF header from.
        open_mode : str
            Opening mode for the file

        Returns
        -------
        BDFHeader
            The resulting BDFHeader
        """
        with open(path, open_mode) as fp:
            return BDFHeader.from_fp(fp)

    def __setattr__(self, key, value):  # noqa: D105
        if key not in self.MAPPING:
            return super().__setattr__(key, value)
        info_d = self.MAPPING[key]
        if not isinstance(value, (tuple, list)):
            value = [value]
        boundaries = self._parse_boundaries(info_d["boundaries"])
        parser = info_d["parser"]
        for index, (start, end) in enumerate(boundaries):
            self.data = (
                self.data[:start]
                + parser.to_bytes(value[index], end - start)
                + self.data[end:]
            )

    def __getattr__(self, item):  # noqa: D105
        if item not in self.MAPPING:
            return super(BDFHeader, self).__getattr__(item)
        info_d = self.MAPPING[item]
        boundaries = self._parse_boundaries(info_d["boundaries"])
        parser = info_d["parser"]
        result = []
        for start, end in boundaries:
            result += [parser.from_bytes(self.data[start:end])]

        if len(result) == 1:
            return result[0]
        else:
            return result

    def _parse_boundaries(
        self,
        boundaries: Tuple[
            Union[int, Tuple[int, str, int]], Union[int, Tuple[str, int]]
        ],
    ) -> List[Tuple[int, int]]:
        """Parse the boundary tuples in self.MAPPING.

        Parameters
        ----------
        boundaries : Tuple[
            Union[int, Tuple[int, str, int]], Union[int, Tuple[str, int]]
        ]
            The boundaries in self.MAPPING

        Returns
        -------
        List[Tuple[int, int]]
            Boundary values for fields in the BDF file.
        """
        result = []
        if isinstance(boundaries[0], (tuple, list)):
            start_bound = (
                boundaries[0][0]
                + getattr(self, boundaries[0][1]) * boundaries[0][2]
            )
        else:
            start_bound = boundaries[0]

        if isinstance(boundaries[1], (tuple, list)):
            # Iterate over channels
            for index in range(getattr(self, boundaries[1][0])):
                result += [
                    [
                        start_bound + index * boundaries[1][1],
                        start_bound + (index + 1) * boundaries[1][1],
                    ]
                ]
        else:
            result = [[start_bound, boundaries[1]]]
        return result

    def concatenate(self, other: "BDFHeader"):
        """Concatenate this BDFHeader with another BDFHeader.

        Parameters
        ----------
        other : BDFHeader
            Other BDFHeader to concatenate to this one.

        Raises
        ------
        ValueError
            When the BDFHeaders are not compatible (see
            self.must_equal_for_merge for attributes that should correspond)
        """
        # Do some checks to see if this merger makes sense
        for attr_str in self.must_equal_for_concatenate_attributes:
            attr_self = getattr(self, attr_str)
            attr_other = getattr(other, attr_str)
            if attr_self != attr_other:
                raise ValueError(
                    "'{}' don't match ({} != {})".format(
                        attr_str, attr_self, attr_other
                    )
                )

        # Apply the concatenate actions
        for action_dict in self.concatenate_actions:
            for attr_str in action_dict["attributes"]:
                new_value = action_dict["action"](
                    getattr(self, attr_str), getattr(other, attr_str)
                )
                setattr(self, attr_str, new_value)

    def __eq__(self, other: "BDFHeader") -> bool:
        """Check if this BDFHeader is equal to another.

        Parameters
        ----------
        other : BDFHeader
            Other BDFHeader to compare with

        Returns
        -------
        bool
            True if both BDFHeaders are equal. They are considered equal if
            all attributes (as defined in self.MAPPING) are equal.
        """
        is_equal = True
        for key in self.MAPPING.keys():
            is_equal = is_equal and getattr(self, key) == getattr(other, key)
        return is_equal


class Merger:
    """Object that can merge the BDFs."""

    stop_file_byte = b""
    stop_merge_bytes = b"[STOP MERGE]"

    def __init__(
        self,
        chunk_size: Union[None, int, Literal["record"]] = "record",
        use_multiprocessing: bool = True,
    ):
        """Class to merge BDF files.

        Parameters
        ----------
        chunk_size : Union[None, int, Literal["record"]]
            How many bytes should be read and written in one go. Increasing
            this parameter may speed up the merging process at the cost of
            larger RAM usage. If "record", the chunk_size will be chosen to be
            the size of one data record. This is also the default. If
            chunk_size is None, the full data will be read at once (note that
            this requires sufficient RAM to load all the data from the BDF
            into memory).
        use_multiprocessing : bool
            Whether to use multiprocessing while reading and writing the data
        """
        if chunk_size is not None and chunk_size != "record":
            chunk_size = int(chunk_size)
            if chunk_size < 1:
                raise ValueError(
                    'chunk_size should be "record", '
                    "None or a positive integer."
                )
        self.chunk_size = chunk_size
        self.use_multiprocessing = use_multiprocessing

    def merge(
        self,
        paths_in: Sequence[Union[str, Path]],
        path_out: Union[str, Path],
        header_class: Type[BDFHeader] = BDFHeader,
        read_mode: str = "rb",
        write_mode: str = "wb",
    ):
        """Merge the BDF's in paths_in into a new one (path_out).

        Parameters
        ----------
        paths_in : Sequence[Union[str, Path]]
            The paths that should be converted.
        path_out : Union[str,Path]
            The path for the new BDF
        header_class : Type[BDFHeader]=BDFHeader
            The wrapper class to load BDF headers.
        read_mode : str
            Mode to open files for reading
        write_mode : str
            Mode to open files for writing
        """
        # Start writing the merged file
        logging.info("Start the writing to {}".format(path_out))
        # Prepare output
        os.makedirs(os.path.dirname(os.path.abspath(path_out)), exist_ok=True)

        new_header, data_starting_points = self.read_headers(
            paths_in, header_class, read_mode
        )
        self.write(
            new_header,
            data_starting_points,
            paths_in,
            path_out,
            read_mode,
            write_mode,
        )
        logging.info("Successfully merged all data in {}".format(path_out))

    def write(
        self,
        new_header: BDFHeader,
        data_starting_points: Iterable[int],
        paths_in: Sequence[Union[str, Path]],
        path_out: Union[str, Path],
        read_mode: str,
        write_mode: str,
    ):
        """Write the new BDF file.

        Parameters
        ----------
        new_header : BDFHeader
            Header for the new BDF file
        data_starting_points : Iterable[int]
            The byte offsets where the header ends and the data records start
        paths_in : Sequence[Union[str, Path]]
            Paths of the BDF files that will be merged.
        path_out : Union[str, Path]
            The path to write the new BDF file to.
        read_mode : str
            Read mode for files
        write_mode : str
            Write mode for files.
        """
        if self.chunk_size == "record":
            # BDF's have 24 bit encoding -> 3 bytes per sample
            chunk_size = sum(new_header.samples_per_record) * 3
        else:
            chunk_size = self.chunk_size

        if self.use_multiprocessing:
            queue = multiprocessing.Queue()
            read_process = multiprocessing.Process(
                target=self._read,
                args=(
                    lambda chunk: self._multithreaded_processing(chunk, queue),
                    data_starting_points,
                    chunk_size,
                    paths_in,
                    read_mode,
                    self.stop_file_byte,
                    self.stop_merge_bytes,
                ),
            )
            write_process = multiprocessing.Process(
                target=self._write,
                args=(
                    path_out,
                    write_mode,
                    new_header.data,
                    queue,
                    self.stop_merge_bytes,
                ),
            )
            read_process.start()
            write_process.start()
            read_process.join()
            write_process.join()
            queue.close()

        else:
            write_fp = open(path_out, write_mode)
            write_fp.write(new_header.data)
            self._read(
                lambda chunk: self._singlethreaded_processing(
                    chunk, write_fp, self.stop_merge_bytes
                ),
                data_starting_points,
                chunk_size,
                paths_in,
                read_mode,
                self.stop_file_byte,
                self.stop_merge_bytes,
            )
            write_fp.close()

    @staticmethod
    def _multithreaded_processing(chunk, queue):
        queue.put(chunk)

    @staticmethod
    def _singlethreaded_processing(chunk, write_fp, stop_merge_bytes):
        if chunk == stop_merge_bytes:
            return
        write_fp.write(chunk)

    @staticmethod
    def _read(
        data_processing_fn: Callable,
        data_starting_points: Iterable[int],
        chunk_size: Union[int, Literal["record"]],
        paths_in: Sequence[Union[str, Path]],
        read_mode: str,
        file_stop_byte: bytes,
        stop_merge_bytes: bytes,
    ):
        for path_index, (path, starting_point) in enumerate(
            zip(paths_in, data_starting_points)
        ):
            logging.info(
                "Merging data from {} ({}/{})...".format(
                    path, path_index + 1, len(paths_in)
                )
            )
            start_time = time.time()
            with open(path, read_mode) as read_fp:
                read_fp.seek(starting_point)
                chunk = None
                while chunk != file_stop_byte:
                    chunk = read_fp.read(chunk_size)
                    data_processing_fn(chunk)
            logging.info(
                "Successfully merged data from {} in {:.2f} seconds".format(
                    path, time.time() - start_time
                )
            )
        data_processing_fn(stop_merge_bytes)

    @staticmethod
    def _write(
        path_out: Union[str, Path],
        write_mode: str,
        header_data: bytes,
        queue: multiprocessing.Queue,
        stop_bytes: Union[str, bytes] = b"",
    ):
        """Get data from a queue and write it to a file.

        Parameters
        ----------
        fp : IO
            Filepointer to read from
        queue : multiprocessing.Queue
            Queue to push data to
        stop_bytes: Union[str, bytes]
            If the chunk that is read equals this, the function will return
        """
        with open(path_out, write_mode) as write_fp:
            write_fp.write(header_data)
            while True:
                chunk = queue.get()
                if chunk == stop_bytes:
                    return
                write_fp.write(chunk)

    def read_headers(
        self,
        paths_in: Sequence[Union[str, Path]],
        header_class: Type[BDFHeader],
        read_mode: str,
    ):
        """Read the BDF headers and construct a new, merged version.

        Parameters
        ----------
        paths_in : Sequence[Union[str, Path]]
            Paths of the BDF files that will be merged.
        header_class : Type[BDFHeader]
            Header for the new BDF file
        read_mode : str
            Read mode for files

        Returns
        -------
        Tuple[BDFHeader, Iterable[int]]
            Tuple of the new (merged) BDFHeader and an iterable of the byte
            offsets that mark where the previous headers ended and the data
            records started
        """
        # Loop over and create BDFHeaders.
        logging.info("Reading the BDF headers.")
        new_header = None
        data_starting_points = []
        for path in paths_in:
            # The first header will be used as a template.
            # Don't worry, all changes will NOT be written to disk, but
            # temporarily saved in the BDFHeader.data attribute
            header = header_class.from_path(path, read_mode)
            if new_header is None:
                new_header = header
            else:
                new_header.concatenate(header)
            data_starting_points += [header.bytes_in_header]
        return new_header, data_starting_points


if __name__ == "__main__":
    logging.basicConfig(
        stream=sys.stdout, level=logging.INFO, format="%(message)s"
    )
    # Argument parser
    parser = argparse.ArgumentParser(description="Merge 2 (or more) BDF files")
    parser.add_argument("--out", help="Output BDF file", required=True)
    parser.add_argument(
        "--disable-multiprocessing",
        help="Disable multiprocessing for merging",
        action="store_true",
    )
    parser.add_argument(
        "--chunk-size",
        help="Size of the chunks to read. Default is 1 record at a time",
        default="record",
    )
    parser.add_argument("bdfs", help="BDF's to merge", nargs="+")

    args = parser.parse_args()

    merger = Merger(args.chunk_size, not args.disable_multiprocessing)
    merger.merge(args.bdfs, args.out, BDFHeader, "rb", "wb")
