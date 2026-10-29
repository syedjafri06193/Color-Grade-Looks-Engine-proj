#include <OpenColorIO/OpenColorIO.h>
#include <exception>
#include <iostream>

namespace OCIO = OCIO_NAMESPACE;

// Prints the OpenColorIO version and, if a config path is given (or $OCIO is
// set), validates that config and lists its color spaces and displays.
int main(int argc, char** argv)
{
    std::cout << "OCIO Version: " << OCIO::GetVersion() << "\n";

    try
    {
        OCIO::ConstConfigRcPtr config =
            argc > 1 ? OCIO::Config::CreateFromFile(argv[1]) : OCIO::Config::CreateFromEnv();

        // Throws with a description of the first problem found.
        config->validate();
        std::cout << "Config is valid.\n";

        std::cout << "Color spaces (" << config->getNumColorSpaces() << "):\n";
        for (int i = 0; i < config->getNumColorSpaces(); ++i)
            std::cout << "  " << config->getColorSpaceNameByIndex(i) << "\n";

        std::cout << "Displays (" << config->getNumDisplays() << "):\n";
        for (int i = 0; i < config->getNumDisplays(); ++i)
            std::cout << "  " << config->getDisplay(i) << "\n";
    }
    catch (const std::exception& e)
    {
        std::cerr << "ocio_inspector: " << e.what() << "\n";
        return 1;
    }
    return 0;
}
