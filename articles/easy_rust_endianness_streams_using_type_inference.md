!=!=! Title: Simplifying endianness sensitive file parsers in Rust with Omnom
!=!=! Created: 09-01-2021
!=!=! Tags: Projects

!=!=! Intro: Start
Recently, while creating a TIFF decoder in Rust ran into a frequent issue
in parser legibility - endianness. Typically, a file format will specify an
endianness globally through it's specification, or will include a marker in
it's header to indicate the endianness with which the file was saved. Usually,
at this point a parser devolves into a series of scalar type and endianness
specific calls, such as 'htons', or custom conversion functions like
'read_u32_le', which can reduce legibility and makes implementations more
error prone. This pattern is also difficult to work with in file formats
where both endiannesses are permitted, such as TIFF, where endianness is
selected based on values read from the header. In this article we introduce
an abstraction in Rust which leans on type-inference to abstract away scalar
type specific functions when parsing data from a stream.
!=!=! Intro: End

# TLDR;

Using the abstraction declared below you can abstract away scalar type and endianness specific functions in a Read struct, reducing code from:
```
let x = read_i32_le(stream)?;
let y = read_i32_le(stream)?;
let depth = read_u8(stream)?;
```
To:
```
let mut stream = ByteStream::new(stream, ByteOrder::LittleEndian);
let x: i32 = stream.read()?;
let y: i32 = stream.read()?;
let depth: u8 = stream.read()?;
```

Structure (requires omnom):
```
use std::io::Result;
use omnom::{ReadBytes, ReadExt};

/// Used to decide whether read_be or read_le is called
#[derive(Clone, Copy)]
pub enum ByteOrder {
  LittleEndian,
  BigEndian,
}

/// Structure that holds our read stream and also the mode (byte order) of reading
pub struct ByteStream<R: ReadExt> {
  order: ByteOrder,
  reader: R,
}

impl <R: ReadExt> ByteStream<R> {

  /// Construct a new ByteStream with a specific byte order (LE or BE)
  pub fn new(reader: R, order: ByteOrder) -> Self {
    Self {
      order,
      reader
    }
  }

  /// Read from the stream with the specified order, overriding the ByteStream order
  pub fn read_with_order<B: ReadBytes>(&mut self, order: ByteOrder) -> Result<B> {
    match order {
      ByteOrder::LittleEndian => self.reader.read_le(),
      ByteOrder::BigEndian => self.reader.read_be()
    }
  }

  /// Read function matches on the current read mode and reads using it (either LittleEndian or BigEndian).
  /// Uses methods from omnom library ReadExt to take from the reader
  pub fn read<B: ReadBytes>(&mut self) -> Result<B> {
    self.read_with_order(self.order)
  }
}
```

# Explanation

When declaring Endian specific and scalar type specific functions in order
to read from a file, legibility and error rate is increased. For example,
imagine a hypothetical C program that parses width, height, and bit depth
from an image, we would have the calls:
```
int with = read_i32_le(file);
int height = read_i32_le(file);
char depth = read_u8(file);
```
Here, it is easy to accidentally select the wrong scalar read function,
such as mistaking a `be` for `le`. These issues are often very difficult to
debug in complex formats, where you need to manually trace the program line
by line to spot the mistake.

While many existing solutions in Rust, such as the
[ByteOrder](https://docs.rs/byteorder/1.1.0/byteorder/enum.BigEndian.html)
library, continue the pattern of scalar type specific read and write methods,
it is not necessary with Rust's powerful trait and type inference systems.

Luckily, the excellent library [Omnom](https://docs.rs/omnom/3.0.0/omnom/) presents a good alternative. In Omnom the [ReadBytes](https://docs.rs/omnom/3.0.0/omnom/trait.ReadBytes.html) trait provides a straightforward interface for parsing scalar types from bytes with a given endianness. Omnom then defines the [ReadExt](https://docs.rs/omnom/3.0.0/omnom/trait.ReadExt.html) trait which uses ReadBytes to read scalar values from a stream encoded while accounting for endianness. Using Omnom we can write programs like:
```
let mut buf = Cursor::new(vec![0; 15]);
let x: i32 = buf.read_le()?;
let y: i32 = buf.read_le()?;
let depth: u8 = buf.read_le()?;
```
Here, the `read_le::<i32>` and `read_le::<u8>` methods are automatically selected through
type inference, removing the scalar specific method. Unfortunately, this
doesn't completely solve our issue though, since we still need to spedify
the endianness of each read. This is particularly troublesome with formats
such as TIFF, where endianness is set in the file header, so program state
will change parser endianness.

To remedy this let's declare our own data structure, ByteStream, which takes
any stream that implements ReadExt and an endianness at construction, and
provides a generic interface through a single method: read. We begin by declaring an enum for endianness:
```
#[derive(Clone, Copy)]
pub enum ByteOrder {
  LittleEndian,
  BigEndian,
}
```

Next, we declare our ByteStream structure. Our ByteStream needs to to store the current endianness mode, specifiying which of read_le and read_be will be used when reading, and a value of ReadExt which represents any readable stream that implements the `read_le` and `read_be` omnom methods:
```
pub struct ByteStream<R: ReadExt> {
  order: ByteOrder,
  reader: R,
}
```

We declare our implementation of ByteStream with a ReadExt as a type argument:
```
impl <R: ReadExt> ByteStream<R> {
}
```

Our `new` method is straightforward, consuming a reader and an endianness to build our ByteStream construction:
```
pub fn new(reader: R, order: ByteOrder) -> Self {
  Self {
    order,
    reader
  }
}
```

Next, we declare the method `read_with_order`. This method takes a type that
implements `ReadBytes` as a type parameter, as well as a user specified order
giving us the type signature `pub fn read_with_order<B: ReadBytes>(&mut self,order: ByteOrder) -> Result<B>`. Recall that ReadBytes is the abstraction
that omnom uses to implement order specific read methods for scalars. Here,
we are saying that `read_with_order` is implemented for any type T that
implements the ReadBytes trait and will produce a value of T or an IO error
when executed. It is implemented as:
```
pub fn read_with_order<B: ReadBytes>(&mut self, order: ByteOrder) -> Result<B> {
  match order {
    ByteOrder::LittleEndian => self.reader.read_le(),
    ByteOrder::BigEndian => self.reader.read_be()
  }
}
```
Here, we are taking the order and calling the order-specific read method defined by the trait `ReadExt` to read values in the correct order from the stream.

Finally, we implement the method `read`, which takes the endianness from the structure:
```
pub fn read<B: ReadBytes>(&mut self) -> Result<B> {
  self.read_with_order(self.order)
}
```

With this in place we now have an easy to use structure where endianness is
set at construction and the scalar type does not need to be specified in
the function name. With this we write the following code to implement our
initial example idiomatically:
```
let mut stream = ByteStream::new(file, ByteOrder::LittleEndian);
let x: i32 = stream.read()?;
let y: i32 = stream.read()?;
let depth: u8 = stream.read()?;
```
