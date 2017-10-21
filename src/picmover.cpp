#include "picmover.hpp"

#include <exiv2/exiv2.hpp>

namespace picmover {
inline
namespace PICMOVER_VERSION_STR {

  Files read( const fs::path& path )
  {
    Files files;

    for( fs::directory_iterator it( path ), end; it != end; ++it )
      {
        if( it->status().type() == fs::file_type::regular )
          files.emplace_back( it->path() );
      }

    return files;
  }

  // Copy files
  void copy( const Files& files, const fs::path& destination )
  {
    // Make sure the path exist
    fs::create_directories( destination );

    for( const auto& file : files )
      fs::copy( file, destination );
  }

  auto RegexFilter::operator()( const fs::path& file ) const -> bool
  {
    return std::regex_search( file.string(), m_regex );
  }

  MakerAttribute::MakerAttribute( const Corrections& corrections,
                                  const std::string& default_maker ):
    m_corrections( corrections ),
    m_default_maker( default_maker )
  {}

  auto MakerAttribute::operator()( const fs::path& file ) const -> std::string
  {
    Exiv2::Image::AutoPtr image = Exiv2::ImageFactory::open( file.string() );
    //assert( image.get() != 0 );
    image->readMetadata();

    Exiv2::ExifData& exif_data = image->exifData();

    if( !exif_data.empty() )
      {
        auto it = exif_data.findKey( Exiv2::ExifKey("Exif.Image.Make") );

        if( it != exif_data.end() )
          return correct( it->toString(), m_corrections );
      } 

    return m_default_maker;
  }
  
  auto ModelAttribute::operator()( const fs::path& file ) const -> std::string
  {
    return "";
  }
  
  auto DateAttribute::operator()( const fs::path& file ) const -> std::string
  {
    return "";
  }

  std::string correct( const std::string& str, const Corrections& corrections )
  {
    for( const auto& entry : corrections )
      {
        if( std::regex_search( str, std::get<0>( entry ) ) )
          return std::get<1>( entry );
      }

    return str;
  }

} // namespace vX_Y
} // namespace picmover...
