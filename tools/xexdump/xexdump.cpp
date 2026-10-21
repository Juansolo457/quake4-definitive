// Decrypt and decompress an Xbox 360 XEX with XenonRecomp's loader and write
//   <out>.bin           the mapped image, starting at the image base
//   <out>.sections.txt  name, base, size, flags per section
//   <out>.symbols.txt   symbols the loader knows (import thunks)
//
//   xexdump <default.xex> <out prefix>

#include <cstdio>
#include <fstream>
#include <iterator>
#include <vector>

#include <image.h>

int main(int argc, char** argv)
{
    if (argc != 3)
    {
        std::fprintf(stderr, "usage: xexdump <file.xex> <out prefix>\n");
        return 1;
    }

    std::ifstream in(argv[1], std::ios::binary);
    std::vector<uint8_t> file((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
    if (file.empty())
    {
        std::fprintf(stderr, "cannot read %s\n", argv[1]);
        return 1;
    }

    Image image = Image::ParseImage(file.data(), file.size());
    if (!image.data)
    {
        std::fprintf(stderr, "failed to load image\n");
        return 1;
    }

    const std::string prefix = argv[2];
    std::ofstream(prefix + ".bin", std::ios::binary).write(reinterpret_cast<const char*>(image.data.get()), image.size);

    std::ofstream sections(prefix + ".sections.txt");
    sections << std::hex;
    for (const auto& section : image.sections)
    {
        sections << section.name << " 0x" << section.base << " 0x" << section.size
                 << ((section.flags & SectionFlags_Code) ? " code" : "")
                 << ((section.flags & SectionFlags_Data) ? " data" : "") << "\n";
    }

    std::ofstream symbols(prefix + ".symbols.txt");
    symbols << std::hex;
    for (const auto& symbol : image.symbols)
    {
        symbols << "0x" << symbol.address << " 0x" << symbol.size << " " << symbol.name << "\n";
    }

    std::printf("base 0x%zx size 0x%x entry 0x%zx sections %zu symbols %zu\n",
        image.base, image.size, image.entry_point, image.sections.size(), image.symbols.size());
    return 0;
}
