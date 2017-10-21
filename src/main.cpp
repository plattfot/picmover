#include "picmover.hpp"
#include <iostream>

int main(int argv, char** argc)
{
  // Read in files from path (default to cwd)
  auto path = picmover::fs::current_path();
  auto files = std::move( picmover::read( path ));

  // Filter out files to copy (based on extension)
  const std::regex raw_re("\\.(3fr|ari|arw|bay|crw|cr2|cap|dcs|dcr|"
                          "dng|drf|eip|erf|fff|iiq|k25|kdc|mdc|mef|"
                          "mos|mrw|nef|nrw|obm|orf|pef|ptx|pxn|r3d|"
                          "raf|raw|rwl|rw2|rwz|sr2|srf|srw|x3f)", std::regex::icase );

  auto raw_files = std::move(picmover::filter(files, picmover::RegexFilter(raw_re) ));
  
  // Get creation date on files (metadata -> filename -> current date [warn when using])
  auto maker_groups = std::move( picmover::groupBy( raw_files,  picmover::MakerAttribute()));

  for( const auto& maker : maker_groups )
    {
      std::cout<<std::get<0>(maker)<<":";
      for( const auto& file : std::get<1>(maker))
        std::cout<<" "<<file;
      std::cout<<std::endl;
    }
  // Group by Camera maker
  // group by Camera model
  // Group by Creation date
  // Filter out files (already existing -> user input)
  // Query for names (gps coord -> user input)
  // Copy files
  
  return 0;
}
