ISSUES = [
    (
        "umya-spreadsheet",
        """\
Hey there, hope you're doing well. I've noticed a strange issue which seems to occur in certain circumstances. The library switches my Calibri font in the following spreadsheet to Arial upon loading and saving the file. I created the file in ONLYOFFICE.

Here's the workbook: fonts.xlsx

And the code used to round-trip:

fn main() {
    let book = umya_spreadsheet::reader::xlsx::read("fonts.xlsx").unwrap();
    umya_spreadsheet::writer::xlsx::write(&book, "output.xlsx").unwrap();
}
And the output file: output.xlsx

As you'll see when opening it, the font has been changed to Arial instead of being retained as Calibri.

Cheers
Fotis

The files are attached in the `./issue` directory.
""",
    ),
    (
        "umya-spreadsheet",
        """\
I can write to row 0 rendering an error when Excel tries to load.

```
    let projects = book.get_sheet_by_name_mut("Projects").unwrap();
    row = 0;
...
    projects.get_cell_mut((3, row)).set_value(Utc::now().to_rfc3339());
```

An earlier parsing error sends in row as 0. If this happens and the workbook is saved, Excel will not load the workbook file. While umya can still go in and look at the file, removing row 0 then allows recovery of the workbook file.

You should consider a guard for 0 on row or column values.""",
    ),
    (
        "RustPython",
        """\
Correct representation of the maximum possible float64.

When I run the following code in RustPython, it gives an "inf", but in CPython it gives the correct maximum possible float64.

```
exponent = int("1023")
significand = int("4503599627370495")
mantissa = 1 + significand/2**52
positive = 1
import math
val = math.ldexp(mantissa/2.0, exponent+1) * (1 if positive else -1)
print(str(val))
```
""",
    ),
    (
        "rust-bio",
        """\
I'm building an FMIndex on a full 256 character `u8` alphabet, like so:

```
    fn build_fm_index(&self, mut text: Vec<u8>) -> Self::Index {
        // Rust-bio expects a sentinel character at the end of the text.
        text.push(0);

        let alphabet = (0u8..=255).collect_vec();
        let alphabet = Alphabet::new(alphabet);
        let sa = suffix_array(&text);
        let bwt = Arc::new(bwt(&text, &sa));
        let less = Arc::new(less(&bwt, &alphabet));
        let occ = Arc::new(Occ::new(&bwt, self.occ_sampling_rate, &alphabet));
        let sampled_sa = sa.sample(
            &text,
            bwt.clone(),
            less.clone(),
            occ.clone(),
            self.sa_sampling_rate,
        );
        let fm = FMIndex::new(bwt, less, occ);
        FmIndexBio { fm, sampled_sa }
    }
```

Then, I query arbitrary `&[u8]` patterns via `self.fm.backward_search(pattern.iter())`.

This gives the following error, especially when the pattern ends in a row of many zeros. Other queries where the pattern contains a few sparse zeros work fine, so that in itself does not seem to be a limitation, and also longer rows of zeros in the middle of the pattern seem to work fine.

```
thread 'main' panicked at /home/philae/git/eth/git/forks/rust-bio/src/data_structures/bwt.rs:173:42:
index out of bounds: the len is 779021 but the index is 144115188075855871
stack backtrace:
[...]
   5: <alloc::vec::Vec<T,A> as core::ops::index::Index<I>>::index
             at /rustc/7c2012d0ec3aae89fefc40e5d6b317a0949cda36/library/alloc/src/vec/mod.rs:2912:9
   6: bio::data_structures::bwt::Occ::get
             at /home/philae/git/eth/git/forks/rust-bio/src/data_structures/bwt.rs:173:42
   7: <bio::data_structures::fmindex::FMIndex<DBWT,DLess,DOcc> as bio::data_structures::fmindex::FMIndexable>::occ
             at /home/philae/git/eth/git/forks/rust-bio/src/data_structures/fmindex.rs:233:9
   8: bio::data_structures::fmindex::FMIndexable::backward_search
             at /home/philae/git/eth/git/forks/rust-bio/src/data_structures/fmindex.rs:167:24
```""",
    ),
    (
        "coreutils",
        """---- test_env::test_env_arg_ignore_signal_valid_signals stdout ----
bin: "/build/reproducible-path/rust-coreutils-0.1.0+git20250813.4af2a84/target/debug/coreutils"
run: /build/reproducible-path/rust-coreutils-0.1.0+git20250813.4af2a84/target/debug/coreutils env --ignore-signal=int sleep 1000

thread 'test_env::test_env_arg_ignore_signal_valid_signals' panicked at tests/by-util/test_env.rs:49:14:
failed to send signal: Os { code: 2, kind: NotFound, message: "No such file or directory" }""",
    ),
    (
        "coreutils",
        """---- test_ls::test_device_number stdout ----

thread 'test_ls::test_device_number' panicked at tests/by-util/test_ls.rs:4854:10:
Expect a block/char device""",
    ),
    (
        "coreutils",
        """---- test_tail::test_following_with_pid stdout ----
bin: "/build/reproducible-path/rust-coreutils-0.1.0+git20250813.4af2a84/target/debug/coreutils"
touch: /tmp/.tmpHJKbrQ/f
run: /build/reproducible-path/rust-coreutils-0.1.0+git20250813.4af2a84/target/debug/coreutils tail --pid 34427 -f /tmp/.tmpHJKbrQ/f

thread 'test_tail::test_following_with_pid' panicked at tests/by-util/test_tail.rs:4865:10:
failed to kill sleep command: Os { code: 2, kind: NotFound, message: "No such file or directory" }""",
    ),
]
