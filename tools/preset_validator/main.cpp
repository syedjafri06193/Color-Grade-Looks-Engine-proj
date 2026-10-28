#include <iostream>

// Native schema validation is not implemented yet. Until it is, this tool
// refuses rather than reporting success it has not earned: a validator that
// always says "complete" is worse than none.
//
// Use the Python validator, which checks every preset against
// src/presets/schema/lookpreset.schema.json:
//
//     python3 tools/preset_validator/validate.py <file.json | directory>
int main(int argc, char** argv)
{
    if (argc < 2)
    {
        std::cerr << "Usage: preset_validator <file.json>\n";
        return 1;
    }

    std::cerr << "preset_validator: native validation is not implemented yet.\n"
                 "Use: python3 tools/preset_validator/validate.py " << argv[1] << "\n";
    return 2;
}
